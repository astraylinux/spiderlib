#!/usr/bin/python
#coding=utf8
import time
import socket
import sys
import logging
from pylib import net, spider, util
reload(sys)
sys.setdefaultencoding("utf-8")

net.init_proxy("data/proxy.conf")

class DnsCache(object):
	def __init__(self):
		self._cache = {"report_time":0, "report_gap":300}

	def report(self):
		""" Log the state of the cache, IP number, spend time  etc."""
		logging.info("DNS- ========== DNS report")
		for (domain, info) in self._cache.items():
			if domain == "report_time" or domain == "report_gap":
				continue
			logging.info("DNS- domain: %s", domain)
			logging.info("DNS- lasttime: %s", util.second2date(info["lasttime"]))
			logging.info("DNS- index: %d", info["index"])
			logging.info("DNS- active: %d, limit: %d", info["active"], info["limit"])
			for (ipstr, record) in info["record"].items():
				succeed = record["succeed"] if "succeed" in record else 0
				failed = record["failed"] if "failed" in record else 0
				spend = record["spend"] if "spend" in record else 0
				logging.info("DNS- ip: %s, OK: %s, NO: %s, SPEND: %0.3f",\
						ipstr, succeed, failed, spend)

	def flush(self, domain, d_config=None):
		""" If NDS cache is used too long,  update it."""
		logging.info("DNS- flush_dns")
		try:
			host_ips = socket.getaddrinfo(domain, None, 0, socket.SOCK_STREAM)
		except socket.gaierror:
			return ({"code":999}, "")
		self._cache[domain]["ip"] = []
		self._cache[domain]["limit"] = 10
		if not "active" in self._cache[domain]:
			self._cache[domain]["active"] = 0
		if d_config and "default_dns" in d_config:
			self._cache[domain]["ip"] = d_config["default_dns"]
			self._cache[domain]["limit"] = d_config["spider_thread_num"]

		if host_ips:
			for host_ip in host_ips:
				new_ip = host_ip[4][0]
				if not new_ip in self._cache[domain]["ip"]:
					self._cache[domain]["ip"].append(new_ip)
		self._cache[domain]["lasttime"] = time.time()
		self._cache[domain]["record"] = {}
		self._cache[domain]["index"] = 0

	def get_ip(self, domain, d_config):
		"""
			Get a IP from cache. If too much threads are working for this domain,
			It will wait. Before return the IP, catch a 'semaphore'.
		"""
		dcache = self._cache[domain]
		while self._cache[domain]["active"] >= self._cache[domain]["limit"]:
			time.sleep(1)

		self._cache[domain]["active"] += 1
		if d_config:
			time.sleep(d_config["spider_gap"])
		index = self._cache[domain]["index"]
		self._cache[domain]["index"] += 1
		ips_len = len(self._cache[domain]["ip"])
		match_ip = self._cache[domain]["ip"][index%ips_len]
		return match_ip

	def record(self, domain, match_ip, code, spend):
		""" Record the work state of a ip, and relace a 'semaphore'."""
		self._cache[domain]["active"] -= 1
		if time.time() - self._cache["report_time"] > self._cache["report_gap"]:
			self.report()
			self._cache["report_time"] = time.time()
		result = "failed"
		if code == 200:
			result = "succeed"
		if not match_ip in self._cache[domain]["record"]:
			self._cache[domain]["record"][match_ip] = {\
					"succeed":0, "failed":0, "spend":spend}
			self._cache[domain]["record"][match_ip][result] = 1
			return

		self._cache[domain]["record"][match_ip]["spend"] += spend
		self._cache[domain]["record"][match_ip][result] += 1

	def check_domain(self, domain, d_config=None):
		if not domain in self._cache:
			self._cache[domain] = {"lasttime":0}
		if time.time() - self._cache[domain]["lasttime"] > 3600:
			self.flush(domain, d_config)


DNS = DnsCache()

def _get(url, domain, heads=None, timeout=30, use_proxy=0, d_config=None):
	#使用代理的站点, 按1/use_proxy比率使用代理
	#1/user_proxy will use proxy or use_proxy=0 no use
	if net.G_PROXY_LIST and not use_proxy == 0 and \
			not int(time.time())%use_proxy:
		return net.proxy_get(url, heads, 40)

	#不使用代理的，要做dns缓存
	#if not use proxy,  we save the dns info
	DNS.check_domain(domain, d_config)

	if not heads:
		heads = {}
	heads["host"] = domain
	match_ip = DNS.get_ip(domain, d_config)
	url = url.replace(domain, match_ip)

	start = time.time()
	(header, html) = net.get(url, heads, timeout)
	spend = time.time() - start

	DNS.record(domain, match_ip, header["code"], spend)
	return (header, html)

def get(url, heads=None, encode=False, timeout=30, use_proxy=0, d_config=None):
	if not "/" in url:
		return (-2, "URL error :" + url)
	domain = url.split("/")[2]

	if d_config:
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
