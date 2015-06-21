#!/usr/bin/python
#coding=utf8
import sys
import config
from spiderlib import tools

reload(sys)
sys.setdefaultencoding("utf-8")

def run():
	tools.CONFIG = config
	tools.creat_link_db()
	tools.creat_html_db()
	tools.creat_info_db()

if __name__ == "__main__":
	run()

