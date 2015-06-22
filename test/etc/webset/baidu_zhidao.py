#!/usr/bin/python
#coding=utf-8
from etc import common

CONFIG = {
	#线程数
	"spider_thread_num": 1,
	#只抓站内
	"only_insite": 1,
	#抓取深度
	"max_depth": 100,
	#站点压力控制(秒)
	"spider_gap": 1,
	#站点的默认编码
	"default_code": "gbk",
	#默认DNS ip，手动添加的dns配置
	"default_dns": [
		"180.149.131.104",
		"180.149.133.165",
		"180.149.131.245",
		"220.181.57.233",
		"123.125.65.91",
		"123.125.115.90",
	],
	#禁止的后辍
	"forbidden_suf": ["rar", "pdf", "jpg", "png", "zip",\
			"doc", "xls", "css", "js", "php"],
	#禁止包含的字符串
	"filter_list": ["javascript", "&lm="],
	#必需包含其中任一个字符串
	"include_list": ["/search?", "/question/"],
	#必需包含其中所有字符串
	"include_must": [],
	#要这些符号后面的都截掉
	"cut_list": ["#"],
	#动态页保留的参数
	#例{"http://www.soku.com/v":["curpage","keyword","limit_date","orderby"]}
	"params_keep": {
		"^http://zhidao.baidu.com/question/[\d]*?\.html": [],
		"^http://zhidao.baidu.com/search": ["word", "pn"],
	},

	#页面匹配正则
	"page_regex": {
		"detail":r"^http://zhidao.baidu.com/question/[\d]*?\.html",
		#"index":"^http://www.23us.com/html/[\d]*/[\d]*/$",
		#"content":"^http://www.23us.com/html/[\d]*/[\d]*/[\d]*.html$"
	},

	"download": {
		"down_table": {"name":"info", "division":1},
		"down_dir": "./data",
		#"default_suf": "jpg",
	},

	"picker":{
		common.G_PAGETYPE["detail"]["type"]:{
			#提取后入的表
			#"table":{"name":"test_info", "division":1},
			#必须要有结果的字段
			"must_key":["title"],
			"path":{
				"title":{"key":"""/html/head/title/text()"""},
				"keywords":{"key":"""/html/head/meta[@name="keywords"]/@content"""},
				"description":{"key":\
					"""/html/head/meta[@name="description"]/@content"""},
			}
		},
		common.G_PAGETYPE["index"]["type"]: {},
		common.G_PAGETYPE["content"]["type"]: {},
	}
}
