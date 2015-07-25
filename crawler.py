#!/usr/bin/python
#coding=utf-8
import sys
import threading
import time
import json
import logging
import net
import re
from pylib import util, sql, expath, spider

reload(sys)
sys.setdefaultencoding = "utf-8"

link_config = {\
	"links":{\
		"type":"list", \
		"block":"//a", \
		"data":{\
			"href":{"key":"./@href"}\
		}\
	}\
}

CONFIG = None

##########################################################################
###								process control
##########################################################################
class Crawler(threading.Thread):
	def __init__(self, num, test=False):
		threading.Thread.__init__(self)
		util.log_config(CONFIG.G_SPIDER_LOG)
		self._num = num
		self._redis = util.get_redis_client(CONFIG.G_REDIS)
		self._sql = sql.Sql(CONFIG.G_MYSQL, CONFIG.G_MAINDB, assoc=True)
		self._site = {}
		self._test = test

	#检查数据是否在数据库里
	def _db_had(self, table_cfg, check_list):
		self._sql.check_connect()
		table = table_cfg["name"]
		division = table_cfg["division"]
		if division == 16 or division == 256:
			ret_dict = {}
			list_dict = {}
			for md5 in check_list:
				flag = md5[-1:] if division == 16 else md5[-2:]
				if flag in list_dict:
					list_dict[flag].append(md5)
				else:
					list_dict[flag] = [md5]
			for key in list_dict:
				has = self._sql.exist(table + key, list_dict[key], "md5")
				ret_dict.update(has)
			return ret_dict
		else:
			return self._sql.exist(table, check_list, "md5")

	#数据加入数据库处理队列
	def _insert2sql(self, links, check_list):
		if self._test:
			return 0
		db_had = self._db_had(CONFIG.G_TABLE_LINK, check_list)
		last_time = time.time()
		table = CONFIG.G_TABLE_LINK["name"]
		division = CONFIG.G_TABLE_LINK["division"]
		print "GET LINK: ", len(links)
		count = 0
		for item in links:
			if item["md5"] in db_had:
				continue

			item["depth"] = self._site["new_depth"]
			item["domain"] = self._site["domain"]
			item["last_time"] = last_time
			sql.data2redis(self._redis, CONFIG.G_SQL_QUEUE, table,\
					"insert", item, "md5", division)
			count += 1
		return count

	#保存html页面到数据库， 分为详情页和过程页，保存可配置
	def _save_html(self, md5, html):
		if self._test:
			return
		if CONFIG.G_IFSAVE_HTML == False:
			return
		if CONFIG.G_IFSAVE_PASS == False and self._site["task"]["type"] !=\
				CONFIG.G_SITE_COMMON.G_PAGETYPE["detail"]["type"]:
			return

		dcode = self._site["config"]["default_code"]
		html = spider.html2utf8(html, dcode)
		item = {"md5":md5, "html":html}
		table = CONFIG.G_TABLE_HTML["name"]
		division = CONFIG.G_TABLE_HTML["division"]
		if not self._db_had(CONFIG.G_TABLE_HTML, {"md5":md5}):
			sql.data2redis(self._redis, CONFIG.G_SQL_QUEUE, table,\
				"insert", item, "md5", division)
		else:
			sql.data2redis(self._redis, CONFIG.G_SQL_QUEUE, table,\
				"update", item, "md5", division)

	#更新状态字段
	def _update_state(self, state, data):
		if self._test:
			return
		data["crawl_state"] = state
		table = CONFIG.G_TABLE_LINK["name"]
		sql.data2redis(self._redis, CONFIG.G_SQL_QUEUE,\
				table, "update", data, "md5")

	#根据后缀和url的内容过滤掉一些不需要的链接
	def _filter_link(self, link):
		d_config = self._site["config"]
		if link.split('.')[-1] in d_config["forbidden_suf"]:
			return True
		for filter_str in d_config["filter_list"]:
			if re.search(filter_str, link):
				return True
		if d_config["include_list"]:
			is_filter = True
			for include_str in d_config["include_list"]:
				if include_str in link:
					is_filter = False
					break
			if is_filter:
				return True
		if d_config["include_must"]:
			for include_str in d_config["include_must"]:
				if not include_str in link:
					return True
		return False

	#解析url，获取url的参数
	def _get_param(self, url):
		params = {}
		if '?' in url:
			pstr = url.split('?')[-1]
			pstrs = pstr.split('&')
			for piece in pstrs:
				if not '=' in piece:
					continue
				argv = piece.split('=')
				params[argv[0]] = argv[1]
			return params
		else:
			return None

	def _url_path_transform(self, link):
		#有路径意义的，做相应的处理，避免重复
		if "/./" in link:
			link = link.replace("/./", "/")
		if "/../" in link:
			pieces = link.split("/")
			index = 0
			for i in range(3, len(pieces)):
				if pieces[i] == "..":
					index = i
			if pieces[index-1] == self._site["domain"]:
				link = link.replace("/..", "")
			else:
				link = link.replace("/../", "").replace(pieces[index-1], "")
		if "//" in link[8:]:
			new = link[0:8]
			for i in range(8, len(link)):
				if link[i] == "/" and new[-1] == "/":
					continue
				new += link[i]
			link = new
		return link

	#按需要修url，（去掉末尾的‘/’，去掉‘#’后面的字符，去掉不保留的参数等）
	def modify_link(self, link):
		d_config = self._site["config"]
		#按配置截去掉不要的部分
		for cut in d_config["cut_list"]:
			link = link.split(cut)[0]
		link = self._url_path_transform(link)

		params = self._get_param(link)
		if params:
			#过滤参数
			link = link.split('?')[0]
			for regex, keeps in d_config["params_keep"].items():
				if not re.search(regex, link):
					continue
				if not keeps:
					break
				pstr = ""
				for key in keeps:
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
	def _get_page_type(self, link):
		for page_type, regular in self._site["config"]["page_regex"].items():
			match = re.search(regular, link)
			if not match:
				continue
			return page_type
		return "unknow"

	#解析页面获取链接的主流程
	def _analyze_html(self, url, html):
		domain = self._site["domain"]
		d_config = self._site["config"]
		xpath = expath.XPath(url, html, code=d_config["default_code"])
		links = xpath.pick(link_config)
		if self._site["new_depth"] > d_config["max_depth"]:
			return "too depth :", self._site["new_depth"]

		link_infos = []
		check_list = []
		for link in links:
			if not "href" in link or not link["href"]:
				continue
			link = link["href"].lower()
			link_domain = link.split("/")[2]
			if d_config["only_insite"] and link_domain != domain:
				continue
			if self._filter_link(link):
				continue
			link = self.modify_link(link)
			type_name = self._get_page_type(link)
			page_type = CONFIG.G_SITE_COMMON.G_PAGETYPE[type_name]["type"]
			md5 = util.md5(link)
			link_infos.append({"md5":md5, "url":link, "type":page_type})
			check_list.append(md5)

		link_infos = util.del_duplicate(link_infos, "md5")
		if self._test:
			return link_infos
		count = self._insert2sql(link_infos, check_list)
		return "[NEWCount]:%d %s"%(count, url)

	#获取调度队列里的任务，调用解析流程，并记录
	def _crawl(self):
		item = self._site["task"]
		md5 = item["md5"]
		url = item["url"]
		last_modified = item["last_modified"]

		headers = {}
		#有last_modified, 且已抓取过的，请求头要加上Last-Modified
		if item["state"] == CONFIG.G_STATUS_CRAWLED and last_modified != "":
			headers["Last-Modified"] = last_modified
		(head, html) = net.get(url, headers, d_config=self._site["config"])
		self._save_html(md5, html)

		if int(head["code"]) == 200:
			ret = self._analyze_html(url, html)
			self._update_state(CONFIG.G_STATUS_CRAWLED, {"md5":md5})
			return ret
		else:
			self._update_state(CONFIG.G_STATUS_ERROR, {"md5":md5})
			return "spider.run: crawl %s %s"%(head["code"], url)

	def _init_site(self, item):
		self._site["task"] = item
		self._site["new_depth"] = int(item["depth"]) + 1
		self._site["domain"] = item["url"].split("/")[2]
		self._site["config"] = CONFIG.G_SITE[self._site["domain"]]

	def run(self):
		while True:
			try:
				self._site = {}
				item = self._redis.rpop(CONFIG.G_NEW_LINK_QUEUE)
				if not item:
					#print "queue is empty"
					time.sleep(5)
					continue
				item = json.loads(item)
				self._init_site(item)
				ret = self._crawl()
				logging.info("[RET]:" + ret)
			except Exception, msg:
				logging.exception(str(msg) + str(item))
				print str(msg), str(item)
				if "MySQL" in str(msg):
					self._sql.check_connect()
				time.sleep(1)
