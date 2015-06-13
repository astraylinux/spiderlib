#!/usr/bin/python
#coding=utf-8
import sys,os
import tb
import re
import HTMLParser
import chardet
import net
import time
import config
import json
import traceback
reload(sys)
sys.setdefaultencoding("utf-8")

url_head = "http://api.easou.com/api/bookapp/chapter_list.m?page_id=1&size=10000&cid=eef_easou_book&version=002&os=android&appverion=1009&nid="

#================================================================  目录信息的基类
class Chapter_basic:
	def __init__(self):
		self.url = ""
		self.domain = ""
		self.conf = ""
	
	def reset(self,url):
		self.url = url
		self.domain = url.split("/")[2]
		self.conf = config.site[self.domain]
		
	#将内容页的url转为详情页的url
	def url_content2index(self,url):
		domain = url.split("/")[2]
		dconfig = config.site[domain]
		for item in  dconfig.index_url_deal:
			for key,val in item.items():	
				if key == "replace_split":
					url = url.replace(url.split(val["key"])[val["index"]],"")
				if key == "ifreplace":
					if not val["new"] in url:
						url = url.replace(val["old"],val["new"])
				if key == "replace":
					url = url.replace(val["old"],val["new"])
				if key == "resub":
					url = re.sub(val["reg"],val["sub"],url)
				if key == "func":
					return dconfig.url2index(url)
		return url

	#章节url加工成完整路径
	def deal_curl(self,head_url,curl):
		if len(curl) == 0:
			return "" 
		if "http://" in curl:
			pass
		elif curl[0] == "/":
			curl = "http://" + self.domain + curl
		else:
			curl = head_url + curl
		if "/../" in curl:
			curl = re.sub("/[\w]+?/\.\./","/",curl)
		return curl

	def get_chapter(self,row,start=True):
		return

#==================================================================== 从源网站抓取章节信息
class Chapter_source(Chapter_basic):
	#html页面做预处理
	def html_pre(self,html):
		html = html.lower()
		#etree 不能处理gb2312，所以要对gb2312的页面做处理
		if tb.spider.html_code(html):
			if tb.spider.html_code(html) == "gb2312":
				html = html.decode("gb2312","ignore").encode("utf-8")
				html = html.replace("gb2312","utf-8")
		else:
			if self.conf.default_charset == "gb2312":
				html = html.decode("gb2312","ignore").encode("utf-8")
				html = html.replace("gb2312","utf-8")
		#整个页面的预处理操作
		if "html_pre" in self.conf.index_config:
			confs = self.conf.index_config["html_pre"]
			for conf in confs:
				if conf["method"] == "replace":
					html = html.replace(conf["argv"][0],conf["argv"][1])
		return html

	#用xpath从html里提取出章节名与链接
	def _get_chapters_url_xpath(self,url,html):
		picker = tb.expath.XPath(url,html)
		site_config = config.site[self.domain]
		ret = picker.pick(site_config.index_config["index_path"])
		if len(ret) == 0 and "block2" in site_config.index_config["index_path"]["chapter"]:
			block2 = site_config.index_config["index_path"]["chapter"]["block2"]
			site_config.index_config["index_path"]["chapter"]["block"] = block2
			ret = picker.pick(site_config.index_config["index_path"])

		name_map = {}
		result = []
		for chapter in ret:
			if not "url" in chapter or not "name" in chapter:
				continue
			curl = chapter["url"]
			name = chapter["name"].strip()
			if not curl or not name:
				continue
			if name in name_map:
				continue	
			if "url_filter" in self.conf.index_config:
				if self.conf.index_config["url_filter"] in curl:
					continue
			curl = self.deal_curl(url,curl)
			result.append({"name":name,"curl":curl})
			name_map[name] = 1
		return result
	
	def get_block(self,url,html):
		block = html
		conf = self.conf.index_config["index_path"]
		block = re.search(conf["block_reg"],html)
		if not block:
			return
		block = block.group()
		return block
	
	def _get_chapters_url_re(self,url,html):
		conf = self.conf.index_config["index_path"]
		code = tb.spider.html_code(html)
		if code:
			html = html.decode(code,"ignore").encode("utf8")
		else:
			html = html.decode(conf["charset"],"ignore").encode("utf8")
		block = self.get_block(url,html)
		if not block:
			print "RE GET REG Block False"
			return []
		match = re.findall(conf["chapter_reg"],block)
		result = []
		name_map = {}
		for chapter in match:
			if "quotes_change" in conf:
				chapter = chapter.replace("'",'"')
			curl = re.search(conf["url_reg"],chapter)
			name = re.search(conf["name_reg"],chapter)
	
			if not curl or not name:
				print curl,name
				continue
			curl = curl.group()
			name = name.group()
			if name in name_map:
				continue
			if "url_filter" in self.conf.index_config:
				if self.conf.index_config["url_filter"] in curl:
					continue
			curl = self.deal_curl(url,curl)
			result.append({"name":name,"curl":curl})
			name_map[name] = 1
		return result

	#内部函数，通过url获取章节目录
	def _get_chapter(self,url,gid=0):
		try:
			self.reset(url)
			#print url
			header = {}
			if "header" in self.conf.index_config:
				header = self.conf.index_config["header"]
			(code,html) = net.Get(url,header)
			retry = 1
			while True:
				if code == 200 or code == 98 or not retry:
					break
				(code,html) = net.Get(url)
				retry -= 1
			if not code == 98:
				time.sleep(config.delay)
			if code != 200:
				print "Get code:",code
				return []
			#html预处理
			html = self.html_pre(html)
			#猎取章节信息
			urls = []
			if "type" in self.conf.index_config and self.conf.index_config["type"] == "re": 
				urls = self._get_chapters_url_re(url,html)
			else:
				urls = self._get_chapters_url_xpath(url,html)
			return urls
		except Exception,e:
			print "source_chapters.get_chapter Exception:",traceback.format_exc()
			return []

	#从源网站抓章节
	def get_append_chapter(self,row,urls,start):
		url = row["last_chapter_url"].strip().rstrip()
		name = row["last_chapter_name"]
		start_index = -1*len(urls)
		last_sort = 1
		if start:
			return [start_index,last_sort]
	
		if "append_by" in self.conf.index_config and self.conf.index_config["append_by"]=="name":
			if urls[-1]["name"] == name:
				return ["Not New"]
			for i in range(1,len(urls)+1):
				if urls[-1*i]["name"] == name:
					start_index = -1*(i-1)
					break;
		else:
			if urls[-1]["curl"] == url:
				return ["Not New"]
			for i in range(1,len(urls)+1):
				new_url = urls[-1*i]["curl"].strip().rstrip()
				if new_url == url:
					start_index = -1*(i-1)
					break;
		last_sort = row["last_sort_chapter"] + 1
		return [start_index,last_sort]

	#从源网站抓章节
	def get_chapter(self,row,start=True):
		url = row["last_chapter_url"]
		gid = row["gid"]
		nid = row["nid"]
		result = []
		url = net.url_pre(url)
		#print url
		
		if not url or not url.split("/")[2] in config.site:
			print "Not in Site:",url
			return []

		self.reset(url)
		#如果有换域名的配置，则试着换
		if "change_host" in self.conf.net:
			change_cfg = self.conf.net["change_host"]
			row["last_chapter_url"] = url.replace(change_cfg["old"],change_cfg["new"])
			url = row["last_chapter_url"]
			self.reset(url)

		chapter_url = self.url_content2index(url) 
		#@@@@@@@
		print chapter_url
		urls = self._get_chapter(chapter_url,gid)
		if not urls:
			print "cb.get_chapter failed",gid,nid,url
			return []
		result = []
	
		appends = self.get_append_chapter(row,urls,start)
		if appends[0] == "Not New":
			return appends
		start_index = appends[0]
		last_sort = appends[1]
		for i in range(start_index,0):
			item = urls[i]
			item["curl"] = urls[i]["curl"].strip().rstrip()
			data = {"gid":gid,"nid":nid,"curl":item["curl"],"chapter_name":item["name"]}
			data["gsort"] = 0
			data["ctype"] = "文"
			data["time"] = int(time.time())*1000
			data["sort"] = last_sort 
			last_sort += 1
			result.append(data)
		return result

#==============================================================  从宜搜抓取章节信息
class Chapter_easou(Chapter_basic):
	#抓取宜搜的目录接口
	def get_chapter(self,row,start):
		retry = 0
		while retry < 3:
			try:
				gid = row["gid"]
				nid = row["nid"]
				url = url_head + str(nid) 
				#print url
				if not start:
					pg = int(row["last_sort"]/25) + 1
					url = url.replace("page_id=1","page_id=%d"%(pg))
					url = url.replace("size=10000","size=25")
				#print row["last_sort"]
				#print url
				(code,html) = net.Get(url)
				if not code == 200:
					print "Crawl from easou Failed"
					retry += 1
					continue
				jset = json.loads(html)
				if not "items" in jset:
					if not "nid: 0" in jset["errorlog"]:
						return ["Not New"]
					print "easou items Error:",gid,nid
					retry += 1
					continue
				return jset["items"]
			except Exception,e:
				print traceback.format_exc()	
				retry += 1
		if retry >= 3:
			return ["easou items Error"]
		else:
			return []
	
#================================================================ 整个模块的对外接口
def get_chapter(row,start=True):
	cb = Chapter_basic()
	if row["chapters_from"] == 0:
		cb = Chapter_easou()
	else:
		cb = Chapter_source()
	return cb.get_chapter(row,start)


#================================================================ 调试
if __name__ == "__main__":
	url = sys.argv[1]
	row = {"gid":0,"nid":1,"last_chapter_url":url,"last_sort":1,"last_chapter_name":"","last_sort_chapter":1,"chapters_from":1}
	if url == "gid":
		gid = sys.argv[2]
		nid = sys.argv[3]
		cursor = tb.sql.GetCursor(config.server,"ebook",True)
		row = tb.sql.ExeSelect(cursor,"book_update",["chapters_from","last_chapter_url","last_sort","last_chapter_name","last_sort_chapter"],{"gid":gid,"nid":nid},True)
		row["gid"] = gid 
		row["nid"] = nid
		
	ret = get_chapter(row,True)
	if ret and isinstance(ret[0],dict):
		for item in ret:
			print item["sort"],"##",item["chapter_name"],"##",item["curl"]
			#print item
	else:
		print ret
