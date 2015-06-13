#!/usr/bin/python
#coding=utf-8
import sys,os
import config
import threading
import time
import redis
import json
import logging
import tb
import net
import re
from lxml import etree

link_config = {
	"links":{
		"type":"list",
		"block":"//a",
		"data":{
			"href":{"key":"./@href"}
		}
	}
}
#######################################################################################
###								process control
#######################################################################################
class runSpider(threading.Thread):
	def __init__(self,num):
		threading.Thread.__init__(self)
		tb.util.LogConfig(config.g_spider_log)
		self.num = num
		self.rc = tb.util.GetRedisClient(config.g_redis)
		self.cursor = tb.sql.GetCursor(config.g_mysql,config.g_maindb,dict=True)

	#检查连接，未断掉就重连
	def _is_connect(self):
		self.cursor = tb.sql.is_connect(self.cursor,config.g_mysql,config.g_maindb,dict=True)

	#检查数据是否在数据库里
	def _db_had(self,check_list):
		self._is_connect()
		table = config.g_table_link["name"]
		division = config.g_table_link["division"]
		return tb.sql.isInDatabase(self.cursor,table,check_list,division,"md5")

	#数据加入数据库处理队列
	def _insert2sql(self,links,check_list,new_depth,domain):
		db_had = self._db_had(check_list)
		last_time = time.time()
		table = config.g_table_link["name"]
		division = config.g_table_link["division"]
		print "GET LINK: ",len(links)
		count = 0
		for item in links:
			if item["md5"] in db_had:
				continue
			#print self.num,item["md5"],item["url"],item["type"]	
			item["depth"] = new_depth
			item["domain"] = domain
			item["last_time"] = last_time
			tb.sql.data2redis(item,self.rc,config.g_sql_queue,table,"insert","md5",division)
			count += 1
		return count
	
	def _update_state(self,state,data):
		data["crawl_state"] = state
		table = config.g_table_link["name"]
		tb.sql.data2redis(data,self.rc,config.g_sql_queue,table,"update","md5")

	#根据后缀和url的内容过滤掉一些不需要的链接
	def _filter_link(self,link,d_config):
		if link.split('.')[-1] in d_config.forbidden_suf:
			return True
		for filter_str in d_config.filter_list:
			if re.search(filter_str,link):
				return True	
		if d_config.include_list:
			isFilter = True 
			for include_str in d_config.include_list:
				if include_str in link:
					isFilter = False
					break
			if isFilter:
				return True
		if d_config.include_must:
			for include_str in config.include_must:
				if not include_str in link:
					return True
		return False 

	#解析url，获取url的参数
	def _get_param(self,url):
		params = {}
		if '?' in url:
			pstr = url.split('?')[-1]
			pstrs = pstr.split('&')
			for p in pstrs:
				ps = p.split('=')
				params[ps[0]] = ps[1]
			return params
		else:
			return None

	def _url_path_transform(self,link,domain):
		#有路径意义的，做相应的处理，避免重复
		if "/./" in link:
			link = link.replace("/./","/")
		if "/../" in link:
			sp = link.split("/")
			index = 0
			for i in range(3,len(sp)):
				if sp[i] == "..":
					index = i
			if sp[index-1] == domain:
				link = link.replace("/..","")
			else:
				link = link.replace("/../","").replace(sp[index-1],"")
		if "//" in link[8:]:
			new = link[0:8]
			for i in range(8,len(link)):
				if link[i] == "/" and new[-1] == "/":
					continue
				new += link[i]
			link = new
		return link

	#按需要修url，（去掉末尾的‘/’，去掉‘#’后面的字符，去掉不保留的参数等）
	def _modify_link(self,link,d_config,domain):
		#按配置截去掉不要的部分
		for cut in d_config.cut_list:
			link = link.split(cut)[0]
		link = self._url_path_transform(link,domain)
			
		params = self._get_param(link)
		if params:  
			#过滤参数
			link = link.split('?')[0]
			if link in d_config.params_keep:
				pstr = ""
				for key in d_config.params_keep[link]:
					if key in params:
						pstr = pstr + key + '=' + params[key] + '&'
				if len(pstr):
					pstr = pstr[:-1]
					link = link + '?' + pstr
		#去掉末尾的/，避免重复
		while str(link).endswith('/'):
			link = str(link)[:-1]
		return link

	#根据配置里的正则表达式判断链接的类型
	def _page_type(self,url,d_config):
		for type,regular in d_config.link_type_config.items():
			match = re.search(regular,url)
			if not match:
				continue
			return type
		return "unknow"

	#解析页面获取链接的主流程
	def _analyze_html(self,url,html,new_depth,type):
		domain = url.split("/")[2]
		d_config = config.g_site[domain]
		xpath = tb.expath.XPath(url,html)
		links = xpath.pick(link_config)
		links = tb.util.DuplicateList(links,"href")
		if new_depth > d_config.max_depth:
			return "too depth :",new_depth

		link_infos = []
		check_list = []
		for link in links:
			if not "href" in link or not link["href"]:
				continue
			link = link["href"].lower()
			link_domain = link.split("/")[2]
			if d_config.only_insite and link_domain!=domain:
				continue	
			if self._filter_link(link,d_config):
				continue	
			link = self._modify_link(link,d_config,domain)
			type_name = self._page_type(link,d_config)
			type = config.g_site_common.G_PAGETYPE[type_name]["type"]
			md5 = tb.util.GetMd5(link)
			link_infos.append({"md5":md5,"url":link,"type":type})
			check_list.append({"md5":md5})

		count = self._insert2sql(link_infos,check_list,new_depth,domain)
		return "[NEWCount]:%d %s"%(count,url)

	#获取调度队列里的任务，调用解析流程，并记录
	def _run(self,item):
		header = {}
		md5 = item["md5"]
		url = item["url"]
		type = item["type"]
		last_modified = item["last_modified"]
		new_depth = int(item["depth"]) + 1
		#有last_modified,且已抓取过的，请求头要加上Last-Modified
		if item["state"] == config.G_STATUS_CRAWLED and last_modified!="":
			header["Last-Modified"] = last_modified
		(head,html) = net.Get(url,header)
		if int(head["code"]) == 200:
			ret = self._analyze_html(url,html,new_depth,type)
			self._update_state(config.G_STATUS_CRAWLED,{"md5":md5})
			return ret
		else:
			self._update_state(config.G_STATUS_ERROR,{"md5":md5})
			return "spider.run: crawl %s %s"%(head["code"],url)

	def run(self):
		while True:
			item = ""
			try:
				item = self.rc.rpop(config.g_newlink_queue)		
				if not item:
					#print "queue is empty"
					time.sleep(5)
					continue
				item = json.loads(item)
				ret = self._run(item)
				logging.info("[RET]:" + ret)
			except Exception,e:
				logging.exception(str(e) + str(item))
				print str(e) ,str(item)
				if "MySQL" in str(e):
					self.cursor.close()
					self.cursor = tb.sql.GetCursor(config.runmysql,config.work_db)
			
#########################################################################################
###								start run
#########################################################################################
if __name__ == "__main__":
	if len(sys.argv) > 1:
		url = sys.argv[1]
		domain = url.split("/")[2]
		d_config = config.g_site[domain]
		rs = runSpider(0)
		print rs._modify_link(url,d_config,domain)
	else:
		for index in range(0,config.g_max_spider_thread):
			thread = runSpider(index)
			thread.start()
		time.sleep(1)
