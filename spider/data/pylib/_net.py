#!/usr/bin/python
#coding=utf-8
import urllib
import urllib2
import gzip
import time
import random
import StringIO
import sys
import traceback
codes = ["301","302","303","304","307","400","404","401","403","405","406","408"
			"500","501","502","503","504","505"]
no_retry = [301,302,303,304,307,400,401,403,404,405,406,500,501,502,503,504,505]

#======================================================== 网络 
def DeGzip(data):
	cmps = StringIO.StringIO(data)
	gzipper = gzip.GzipFile(fileobj=cmps)
	return gzipper.read()

def Post(url,data,heads = {},datatype=True):
	try:
		request = urllib2.Request(url)
		data = urllib.urlencode(data)
		for key in heads:
			request.add_header(key, heads[key])
		response = urllib2.urlopen(request,data,timeout=10)
		code = response.getcode()
		headerinfo = response.info()
		rep_header["code"] = code
		for key,val in headerinfo.items():
			rep_header[key] = val
		if datatype:
			return (rep_header,response.read())
	except Exception,e:
		if "404" in str(e):
			return ({"code":404},"")
		else:
			return ({"code":-1},"")

def _get_error_code(e_str):
	for code in codes:
		if code in e_str:
			return int(code)
	if "page not find" in e_str:
		return 404
	return -1

def Get(url,heads={},timeout=12):
	fails=0
	html=""
	rep_header = {}
	headerinfo = {}
	code=200
	last_error = 0
	while True:
		try:
			if fails>=3:
				break
			request=urllib2.Request(url)
			request.add_header("version","HTTP/1.1")
			request.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36")
			request.add_header("Accept-Encoding","identity")
			for key in heads:
				request.add_header(key,heads[key])
			res_page=urllib2.urlopen(request,timeout=timeout)
			code=res_page.getcode()
			headerinfo=res_page.info()
			if ("Content-Length" in headerinfo) and int(headerinfo['Content-Length'])>10048576:
				code=99
				html=""
			else:
				html=res_page.read()
			if "Content-Encoding" in headerinfo and 'gzip' in headerinfo["Content-Encoding"]:
				html=DeGzip(html)
			break
		except Exception,e:
			last_error = str(e)
			code = _get_error_code(str(e))
			if code in no_retry:
				rep_header["code"] = code
				return (rep_header,"")
			fails = fails + 1
			time.sleep(0.5)
	rep_header["code"] = code
	for key,val in headerinfo.items():
		rep_header[key] = val
	return (rep_header,html)

#指定要返回gzip编码的数据的get
def Get_gzip(url,heads={}):
	heads["Accept-Encoding"] = "gzip"
	(code,html) = Get(url, heads)
	if code ==200:
		html = DeGzip(html)
	return (code,html)

#================================ 使用代理
#使用代理，先调用InitProxy载入代理配置文件
#配置文件格式 ip:port\tdescription
#ProxyGet和Post会随机调用代理列表中的代理
g_proxy_list = [] 
def InitProxy(proxy_file):
	f_proxy = open(proxy_file,"r+")
	lines = f_proxy.readlines()	
	f_proxy.close()
	count = 0
	for line in lines:
		if line[0] == "#":
			continue
		line = line.replace("\t"," ")
		line = line.replace("\n","")
		ip = line.split(" ")[0]
		desc = line.split(" ")[-1]
		proxy = {"http":ip,"count":count,"desc":desc}
		count = count + 1
		g_proxy_list.append(proxy)

def ProxyPost(url,data,heads = {},datatype=True):
	retry = 3 
	rep_header = {}
	headerinfo = {}
	proxy = g_proxy_list[random.randint(0,len(g_proxy_list)-1)]		
	proxy_handler = urllib2.ProxyHandler(proxy)
	opener = urllib2.build_opener(proxy_handler)
	request = urllib2.Request(url)
	data = urllib.urlencode(data)
	code = 200
	for key in heads:
		request.add_header(key, heads[key])
	while retry:
		try:
			response = opener.open(request,data,timeout=10)
			code = response.getcode()
			headerinfo = response.info()
			if datatype:
				return ({"code":code},response.read())
			else:
				return ({"code":code},response)
		except Exception,e:
			retry = retry - 1
			time.sleep(1)
			code = _get_error_code(str(e))
			if code in no_retry:
				rep_header["code"] = code
				return (rep_header,"")
	rep_header["code"] = code
	for key,val in headerinfo.items():
		rep_header[key] = val
	return (rep_header,html)

def ProxyGet(url,heads = {},datatype=True):
	retry = 3 
	rep_header = {}
	headerinfo = {}
	proxy = g_proxy_list[random.randint(0,len(g_proxy_list)-1)]		
	proxy_handler = urllib2.ProxyHandler(proxy)
	opener = urllib2.build_opener(proxy_handler)
	request = urllib2.Request(url)
	for key in heads:
		request.add_header(key, heads[key])
	while retry:	
		try:
			response = opener.open(request,timeout=10)
			code = response.getcode()
			if datatype:
				headerinfo = response.info()
				headerinfo["code"] = str(code)
				html = response.read()
				if "Content-Encoding" in headerinfo and 'gzip' in headerinfo["Content-Encoding"]:
					html = DeGzip(html)
				return (headerinfo,html)
			else:
				return (headerinfo,response)
		except Exception,e:
			retry = retry - 1 
			if "304" in str(e):
				rep_header["code"] = 304
				return (rep_header,"")
			time.sleep(1)
			if retry == 0:
				print proxy
				print traceback.format_exc(str(e))
				if "404" in str(e):
					return ({"code":404},"")
				else:
					return ({"code":-1},"")
	rep_header["code"] = code
	for key,val in headerinfo.items():
		rep_header[key] = val
	return (rep_header,html)
	
#========================================================= 下载文件
def DownloadFile(url,local,head=None):
	retry = True
	while retry:
		try:
			request = urllib2.Request(url)
			if head:
				for key,value in head.items():
					request.add_header(key,value)
			uf = urllib2.urlopen(request, timeout=10)
			tmpdata = uf.read(64*1024)
			of = open(local,"wb+")
			while tmpdata:
				of.write(tmpdata)
				tmpdata = uf.read(64*1024)
			of.close()
			uf.close()
			return True
		except Exception,e:
			#print e
			retry = False	
		return False
	
