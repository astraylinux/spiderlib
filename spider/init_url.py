#!/usr/bin/python
#coding=utf8
import os,sys
import tb
import config
from spiderlib import tools
reload(sys)
sys.setdefaultencoding("utf-8")


#when the link table empty, you can't use this to add a base url
#the spider will start crawl by it
#init_url.py 'base_url' 

tools.config = config
url = sys.argv[1]
print tools.init_url(url)
