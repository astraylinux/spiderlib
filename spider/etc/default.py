#!/usr/bin/python
#coding=utf-8
import common

CONFIG = {
	#线程数
	"spider_thread_num": 4,
	#只抓站内
	"only_insite": 1,
	#抓取深度
	"max_depth": 20,
	#站点压力控制(秒)
	"spider_gap": 0.5,
	#站点的默认编码
	"default_code": "gbk",
	#禁止的后辍
	"forbidden_suf": ["rar", "pdf", "jpg", "png", "zip",\
			"doc", "xls", "css", "js", "php"],
	#禁止包含的字符串
	"filter_list": ["javascript",".php",".html#"],
	#必需包含其中任一个字符串
	"include_list": [],
	#必需包含其中所有字符串
	"include_must": [],
	#要这些符号后面的都截掉
	"cut_list": ["#"],
	#动态页保留的参数
	#例{"http://www.soku.com/v":["curpage","keyword","limit_date","orderby"]}
	"params_keep": {},

	#页面匹配正则
	"page_type": {
		"detail":r"^http://www.23us.com/book/[\d]*$",
		#"index":"^http://www.23us.com/html/[\d]*/[\d]*/$",
		#"content":"^http://www.23us.com/html/[\d]*/[\d]*/[\d]*.html$"
	},

	"picker":{
		common.G_PAGETYPE["detail"]["type"]:{
			#提取后入的表
			"table":{"name":"info", "division":1},
			#必须要有结果的字段
			"must_key":["title"],
			"path":{
				#普通结果
				"title":{"key":\
					"""/html/body//h1[@class="article-title"]/a/text()"""},
				#有对结果做处理
				"date":{"key":"""/html//div[@class="meta"]/time/text()""",
						"remake":[{"method":"replace", "argv":["日", ""]}]},
				#取得的是列表
				"tags":{
					"type":"list",
					"block":"""/html//div[@class="article-tags"]/a""",
					"data":{"tags":{"key":"./text()"}}
				}
			}
		},
		common.G_PAGETYPE["index"]["type"]: {},
		common.G_PAGETYPE["content"]["type"]: {},
	}
}
