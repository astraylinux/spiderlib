#!/usr/bin/python
#coding=utf-8
import config
import time
from spiderlib import crawler


if __name__ == "__main__":
	crawler.CONFIG = config
	for index in range(0, config.G_MAX_SPIDER_THREAD):
		thread = crawler.Crawler(index)
		thread.start()
		time.sleep(1)
	time.sleep(1)

