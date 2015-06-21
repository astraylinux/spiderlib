#!/usr/bin/python
#coding=utf8
"""
when the link table empty, you can't use this to add a base url
the spider will start crawl by it
init_url.py 'base_url'
"""
import sys
import config
from spiderlib import tools
reload(sys)
sys.setdefaultencoding("utf-8")

tools.CONFIG = config
url = sys.argv[1]
print tools.init_url(url)
