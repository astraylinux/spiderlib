#!/usr/bin/python
#coding=utf8
import time
import socket
import sys
import logging
from pylib import net, spider, util
reload(sys)
sys.setdefaultencoding("utf-8")

DOMAINS = {}
BLACK = []
DNS_CACHE = {"report_time":0, "report_gap":300}
net.init_proxy("data/proxy.conf")

def dns_report():
	logging.info("DNS-========== DNS report")
	for (domain, info) in DNS_CACHE.items():
		if domain == "report_time" or domain == "report_gap":
			continue
		logging.info(domain)
		logging.info("DNS- lasttime: %s", util.second2date(info["lasttime"]))
		logging.info("DNS- index: %d", info["index"])
		for (ipstr, record) in info["record"].items():
			succeed = record["succeed"] if "succeed" in record else 0
			failed = record["failed"] if "failed" in record else 0
			spend = record["spend"] if "spend" in record else 0
			logging.info("DNS- ip: %s, OK: %s, NO: %s, SPEND: %0.3f",\
					ipstr, succeed, failed, spend)

def _flush_dns(domain, d_config=None):
	#DNS缓存超过1小时，就重新缓存
	#if nds cache use time more than 1 hour,  update it
	logging.info("DNS- flush_dns")
	try:
		host_ips = socket.getaddrinfo(domain, None, 0, socket.SOCK_STREAM)
	except socket.gaierror:
		return ({"code":999}, "")
	if host_ips:
		DNS_CACHE[domain]["ip"] = []
		if d_config and "default_dns" in d_config:
			DNS_CACHE[domain]["ip"] = d_config["default_dns"]
		for host_ip in host_ips:
			new_ip = host_ip[4][0]
			if not new_ip in DNS_CACHE[domain]["ip"]:
				DNS_CACHE[domain]["ip"].append(new_ip)
	DNS_CACHE[domain]["lasttime"] = time.time()
	DNS_CACHE[domain]["record"] = {}
	DNS_CACHE[domain]["index"] = 0

def get_ip_from_cache(domain):
	index = DNS_CACHE[domain]["index"]
	DNS_CACHE[domain]["index"] += 1
	ips_len = len(DNS_CACHE[domain]["ip"])
	match_ip = DNS_CACHE[domain]["ip"][index%ips_len]
	return match_ip

def result_record(domain, match_ip, code, spend):
	if time.time() - DNS_CACHE["report_time"] > DNS_CACHE["report_gap"]:
		dns_report()
		DNS_CACHE["report_time"] = time.time()
	result = "failed"
	if code == 200:
		result = "succeed"
	if not match_ip in DNS_CACHE[domain]["record"]:
		DNS_CACHE[domain]["record"][match_ip] = {\
				"succeed":0, "failed":0, "spend":spend}
		DNS_CACHE[domain]["record"][match_ip][result] = 1
		return

	DNS_CACHE[domain]["record"][match_ip]["spend"] += spend
	DNS_CACHE[domain]["record"][match_ip][result] += 1

def _get(url, domain, heads=None, timeout=30, use_proxy=0, d_config=None):
	#使用代理的站点, 按1/use_proxy比率使用代理
	#1/user_proxy will use proxy or use_proxy=0 no use
	if net.G_PROXY_LIST and not use_proxy == 0 and \
			not int(time.time())%use_proxy:
		return net.proxy_get(url, heads, 40)

	#不使用代理的，要做dns缓存
	#if not use proxy,  we save the dns info
	if not domain in DNS_CACHE:
		DNS_CACHE[domain] = {"lasttime":0}
	if time.time() - DNS_CACHE[domain]["lasttime"] > 3600:
		_flush_dns(domain, d_config)

	if not heads:
		heads = {}
	heads["host"] = domain
	match_ip = get_ip_from_cache(domain)
	url = url.replace(domain, match_ip)
	start = time.time()
	(header, html) = net.get(url, heads, timeout)
	spend = time.time() - start
	result_record(domain, match_ip, header["code"], spend)
	return (header, html)

def _redis_contral(url, domain, heads, timeout, use_proxy, d_config):
	#rc = util.get_redis_client(config.g_redis)
	#rkey = domain + "_threads"
	#while rc.get(rkey) >= str(domain_config["spider_thread_num"]):
	#	time.sleep(1)
	#time.sleep(domain_config["spider_gap"])
	#rc.incr(rkey)
	#result = _get(url, domain, heads, timeout, use_proxy, d_config)
	#rc.decr(rkey)
	#return result
	return

def get(url, heads=None, encode=False, timeout=30, use_proxy=0, d_config=None):
	if not "/" in url:
		return (-2, "URL error :" + url)
	domain = url.split("/")[2]

	if d_config:
		time.sleep(d_config["spider_gap"])
		result = _get(url, domain, heads, timeout, use_proxy, d_config)
		if encode == True:
			(info, html) = result
			html = spider.html2utf8(html, d_config["default_code"])
			result = (info, html)
		return result
	else:
		return _get(url, domain, heads, timeout, use_proxy)

if __name__ == "__main__":
	if len(sys.argv) == 2:
		qheaders = {}
		#qheaders = {"If-Modified-Since":"Wed,  15 Oct 2014 07:51:23 GMT"}
		#qheaders = {"If-None-Match":"80c2d1d04ce8cf1:0"}
		#qheaders = {"If-Modified-Since":"Thu,  16 Oct 2014 02:41:28 GMT"}
		(rheads, rhtml) = get(sys.argv[1], qheaders, encode=True)
		#print rhtml
		print rheads["code"], len(rhtml)
