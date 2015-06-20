#!/usr/bin/python
#coding=utf8
"""
对spiderlib进行单元测试，不过这是后面加的，
有些东西就没有测得很详细
"""
import config
from pylib import sql
from spiderlib import tools, net


config.g_mysql["pw"] = "wtf2222"
cursor = sql.GetCursor(config.g_mysql, config.g_maindb, dict=True)
tools.config = config
net.config = config

def print_flag(flag):
	print "#"*50, flag

def creater_test():
	print_flag("creater_test")
	link = tools.creat_link_db()
	html = tools.creat_html_db()
	info = tools.creat_info_db()
	if not link:
		print "create table 'link' failed!"
	if not html:
		print "create table 'html' failed!"
	if not info:
		print "create table 'info' failed!"

def init_url_test():
	print_flag("init_url_test")
	url = "http://www.iphone6wallpaper.com"
	ret = tools.init_url(url)
	if not ret:
		print "init failed, ret: 0"
		return

	row = sql.ExeSelect(cursor, config.g_table_link["name"], ["id"], {"url":url})
	if not row:
		print "ret is ok, but url not exist"

def net_get_test():
	print_flag("net_get_test")
	url = "http://www.google.com"
	(header, html) = net.Get(url, heads={}, encode=False, timeout=30, use_proxy=0)
	if not int(header["code"]) == 200:
		print "get code :", header["code"]
		return
	if len(html) < 500:
		print "html too short:", len(html)
		print html

def net_get_with_proxy_test():
	print_flag("net_get_with_proxy_test")
	url = "http://www.baidu.com"
	(header, html) = net.Get(url, heads={}, encode=False, timeout=30, use_proxy=1)
	if not int(header["code"]) == 200:
		print "get code :", header["code"]
		return
	if len(html) < 500:
		print "html too short:", len(html)
		print html

def net_get_with_domain_test():
	print_flag("net_get_with_domain_test")
	url = "http://www.baidu.com"
	domain = {"spider_gap":1, "spider_thread_num":2, "default_code":"utf8"}
	(header, html) = net.Get(url, {}, encode=True, timeout=30,\
							use_proxy=0, domain_config=domain)
	if not int(header["code"]) == 200:
		print "get code :", header["code"]
		return
	if len(html) < 500:
		print "html too short:", len(html)
		print html

def sqld_test():
	pass

def _test():
	print_flag("_test")

if __name__ == "__main__":
	SWITCH = "sql"
	if SWITCH == "all" or SWITCH == "tools":
		creater_test()
		init_url_test()

	if SWITCH == "all" or SWITCH == "net":
		net_get_test()
		net_get_with_proxy_test()
		net_get_with_domain_test()

	if SWITCH == "all" or SWITCH == "net":
		sqld_test()

	cursor.close()

