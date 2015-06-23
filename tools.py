#!/usr/bin/python
#coding=utf8
import sys
import time
from pylib import sql, util
reload(sys)
sys.setdefaultencoding("utf-8")

CONFIG = None

def init_url(url, sql_agent=None):
	"""
		when the link table empty, you can't use this to add a base url
		the spider will start crawl by it
		init_url.py 'base_url'
	"""
	if sql_agent == None:
		sql_agent = sql.Sql(CONFIG.G_MYSQL, CONFIG.G_MAINDB)
	data = {}
	data["url"] = url
	data["md5"] = util.md5(url)
	data["depth"] = 0
	data["type"] = 0
	data["last_time"] = int(time.time())
	data["domain"] = url.split("/")[2]
	ret = sql_agent.insert(CONFIG.G_TABLE_LINK["name"], data)
	return (sql_agent, ret)

def creat_link_db():
	"""
		table which save then base url and new url we find
		ink表基本上是通用的，可以直接使用，不需要修改
	"""
	sql_agent = sql.Sql(CONFIG.G_MYSQL, CONFIG.G_MAINDB)
	for i in range(0, CONFIG.G_TABLE_LINK["division"]):
		table = CONFIG.G_TABLE_LINK["name"]
		if CONFIG.G_TABLE_LINK["division"] > 1:
			table = table + str(i)
		link_sql = """CREATE TABLE `%s` (
			  `id` int(11) NOT NULL AUTO_INCREMENT,
			  `md5` char(32) NOT NULL,
			  `domain` char(64) NOT NULL,
			  `url` char(255) NOT NULL,
			  `type` smallint(6) NOT NULL COMMENT '页面类型，0:中间页(process page)，1:详情页(detail page)等',
			  `depth` smallint(6) NOT NULL COMMENT '页面的深度',
			  `last_time` int(11) DEFAULT NULL,
			  `uptimes` int(11) DEFAULT '0',
			  `un_uptimes` int(11) DEFAULT '0',
			  `last_modified` char(32) DEFAULT '' COMMENT '网站的last_modified,静态页面可用',
			  `crawl_state` smallint(6) DEFAULT '0' COMMENT '抓取状态-1:失败(failed),0:未抓(before crawl)，1:成功(succeed)',
			  `pick_state` smallint(6) DEFAULT '0' COMMENT '提取状态-1:失败(failed),0:未提取(before pick)，1:成功(succeed)',
			  `state` smallint(6) DEFAULT '0' COMMENT '扩展用状态字段(extend)',
			  PRIMARY KEY (`id`),
			  UNIQUE KEY `md5` (`md5`) USING BTREE
			) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"""%(table)
		#print link_sql
		return sql_agent.execute(link_sql)

def creat_html_db():
	"""
		table to save all then html if CONFIG.g_ifsave_html is true
		link表基本上是通用的，可以直接使用，不需要修改
	"""
	sql_agent = sql.Sql(CONFIG.G_MYSQL, CONFIG.G_MAINDB)
	for i in range(0, CONFIG.G_TABLE_HTML["division"]):
		table = CONFIG.G_TABLE_HTML["name"]
		if CONFIG.G_TABLE_HTML["division"] > 1:
			table = table + str(i)
		html_sql = """CREATE TABLE `%s` (
			`id` int(11) NOT NULL AUTO_INCREMENT,
			`md5` char(32) NOT NULL,
			`html` text NOT NULL,
			`state` smallint(6) DEFAULT '0' COMMENT '扩展用状态字段(extend)',
			PRIMARY KEY (`id`),
			UNIQUE KEY `md5` (`md5`) USING BTREE
		) ENGINE=MyISAM DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"""%(table)
		#print html_sql
		return sql_agent.execute(html_sql)

def creat_info_db():
	"""
		table of info,the picker pick content and save them in this table
		it has few default fields, you must have to add new fields by hands
		提取后的信息，有些字段是通用的，可以直接生成
	"""
	sql_agent = sql.Sql(CONFIG.G_MYSQL, CONFIG.G_MAINDB)
	for i in range(0, CONFIG.G_TABLE_INFO["division"]):

		table = CONFIG.G_TABLE_INFO["name"]
		if CONFIG.G_TABLE_INFO["division"] > 1:
			table = table + str(i)
		info_sql = """CREATE TABLE `%s` (
		  `id` int(11) NOT NULL AUTO_INCREMENT,
		  `title` char(255) DEFAULT NULL,
		  `md5` char(32) DEFAULT NULL,
		  `url` varchar(512) DEFAULT NULL,
		  `state` int(11) DEFAULT '0' COMMENT '扩展用状态字段(extend)',
		  PRIMARY KEY (`id`),
		  UNIQUE KEY `md5` (`md5`) USING BTREE,
		  KEY `id` (`id`) USING BTREE
		) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;"""%(table)
		#print info_sql
		return sql_agent.execute(info_sql)
