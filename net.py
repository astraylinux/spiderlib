#!/usr/bin/python
#coding=utf8
import os,sys
from SimplePythonLib import net,util,spider
import time
import socket
import sys
import redis

domains = {}
black = []
DNScache = {}

config = None
net.InitProxy("data/proxy.conf")

def _Get(url,domain,heads={},timeout=30,use_proxy=0):
	#使用代理的站点,1/use_proxy比率使用代理
	#1/user_proxy will use proxy or use_proxy=0 no use
	if net.g_proxy_list and not use_proxy==0 and not int(time.time())%use_proxy:
		return net.ProxyGet(url,heads,40)
	#不使用代理的，要做dns缓存
	#if not use proxy, we save the dns info
	if not domain in DNScache:
		DNScache[domain] = {"lasttime":0}
	if time.time() - DNScache[domain]["lasttime"] > 3600:
		#DNS缓存超过1小时，就重新缓存
		#if nds cache use time more than 1 hour, update it
		host_ip = False
		try:
			host_ip = socket.gethostbyname(domain)
		except Exception,e:
			#print >>sys.stderr,e
			return ({"code":999},"")
		if host_ip:
			#print >>sys.stderr,"@@@@@@ ReAnalyze DNS for '%s' get IP:%s"%(domain,host_ip)
			DNScache[domain]["ip"] = host_ip
		DNScache[domain]["lasttime"] = time.time()
	#download page
	heads["host"] = domain
	url = url.replace(domain,DNScache[domain]["ip"])
	#s = time.time()
	(header,html) = net.Get(url,heads,timeout)
	#print time.time() - s
	return (header,html)

def Get(url,heads={},encode=False,timeout=30,use_proxy=0,domain_config=None):
	if not "/" in url:
		return (-2,"URL error :" + url)
	domain = url.split("/")[2]

	if domain_config:
		time.sleep(domain_config["spider_gap"])
		#rc = util.GetRedisClient(config.g_redis)
		#rkey = domain + "_threads"
		#while rc.get(rkey) >= str(domain_config["spider_thread_num"]):
		#	time.sleep(1)
		#time.sleep(domain_config["spider_gap"]
		#rc.incr(rkey)
		result = _Get(url,domain,heads,timeout,use_proxy)
		#rc.decr(rkey)
		if encode == True:
			#deal the char set
			(info,html) = result
			html = spider.html2utf8(html,domain_config["default_code"])
			result = (info,html)
		return result
	else:
		return _Get(url,domain,heads,timeout,use_proxy)

if __name__ == "__main__":
	if len(sys.argv) == 2:
		heads = {}
		#heads = {"If-Modified-Since":"Wed, 15 Oct 2014 07:51:23 GMT"}
		#heads = {"If-None-Match":"80c2d1d04ce8cf1:0"}
		#heads = {"If-Modified-Since":"Thu, 16 Oct 2014 02:41:28 GMT"}
		(header,html) = Get(sys.argv[1],heads,encode=True)
		print html
		print header["code"],len(html)
