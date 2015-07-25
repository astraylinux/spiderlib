#!/usr/bin/python
#coding=utf-8
import sys
import config
import time
import pylib
from spiderlib import crawler


if __name__ == "__main__":
	crawler.CONFIG = config
	if len(sys.argv) > 1 and sys.argv[1] == "test":
		spider = crawler.Crawler(0, test=True)
		item = {}
		item["depth"] = 0
		#item["url"] = "http://wenda.haosou.com/search/?q=%E5%90%83%E9%A5%AD"
		item["url"] = "http://zhidao.baidu.com/search?word=2016%e5%b9%b4%e9%ab%98%e8%80%83%e6%97%b6%e9%97%b4&pn=310"
		item["md5"] = pylib.util.md5(item["url"])
		item["last_modified"] = ""
		item["state"] = 0
		item["type"] = 0
		spider._init_site(item)
		ret = spider._crawl()
		print pylib.util.json_dump(ret)
	else:
		for index in range(0, config.G_MAX_SPIDER_THREAD):
			thread = crawler.Crawler(index)
			thread.start()
			time.sleep(1)
		time.sleep(1)
