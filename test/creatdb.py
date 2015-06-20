#!/usr/bin/python
#coding=utf8
import os,sys
import config
from spiderlib import dbcreater

reload(sys)
sys.setdefaultencoding("utf-8")

def run():
	dbcreater.config = config
	dbcreater.creat_link_db()
	dbcreater.creat_html_db()
	dbcreater.creat_info_db()

if __name__ == "__main__":
	run()

