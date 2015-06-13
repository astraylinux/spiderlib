#!/usr/bin/python
#coding=utf8
import os,sys
import time
import re
import json
import _util
import _net
from lxml import etree
reload(sys)
sys.setdefaultencoding("utf-8")

################################################################## 提取基类
class path_basic:
	#传url是为了提取相对路径的url可以组成完整
	def __init__(self,url,html):	
		self.url = url
		self.html = html
		sp = url.split("/")
		self.domain = sp[2]
		self.url_domain = sp[0] + "//" + sp[2]
		if url[-1] == "/":
			self.path = url
		else:
			self.path = url.replace(url.split("/")[-1],"")
	
	#如果提取结果是http链接，转换成完整路径
	def _merge_url(self,url_sub):
		if not url_sub:
			return 
		if "http://" in url_sub:
			return url_sub
		elif url_sub[0] == "/":
			return str(self.url_domain + url_sub)
		else:
			return str(self.path + url_sub)

	#一些扩展的方法，对xpath的结果再处理,(分割，替换和正则)
	def _ex_func(self,rstr,func):
		method =  func["method"]
		argv = func["argv"]
		if method == "split":
			if not argv[0] in rstr:
				return rstr
			sp = rstr.split(argv[0])
			if "," in argv[1]:
				for index in argv[1].split(","):
					result += sp[int(index)]
			else:
				result = sp[int(argv[1])]
		elif method == "replace":
			result = rstr.replace(argv[0],argv[1])
		elif method == "re":
			match = re.search(argv[0],rstr)	
			result = rstr
			if match:
				result = match.group()
		elif method == "re.sub":
			ret = re.sub(argv[0],argv[1],rstr)
			result = rstr
			if ret:
				result = ret 
		else:
			result = rstr
		return result

	#xpath提取之前做的处理
	def _path_pre(self,val):
		sentence = val["key"]
		return sentence

	#xpath提取完后再做的处理
	def _path_after(self,rstr,val):
		if "remake" in val:
			for func in val["remake"]:
				rstr = self._ex_func(rstr,func)
		path = val["key"]
		if (path[-5:] == "@href" or path[-4:] == "@src") and not "not_abs_url" in val:
			rstr = self._merge_url(rstr)
		return rstr 

	#提取的主要流程
	def _path2array(self,tree,config):
		result = {}
		for key,val in config.items():
			#提取结果为字符串的
			if not "type" in val:
				sentence = self._path_pre(val)
				ret = self._picker(tree,sentence)
				if not ret:
					#result[key] = ret
					continue
				ret = self._path_after(ret[0],val)
				result[key] = ret
			#提取结果list列表
			elif val["type"] == "list":
				rlist = []
				blocks = self._picker(tree,val["block"])
				for block in blocks:
					ret = self._path2array(block,val["data"])
					if ret:
						rlist.append(ret)
				result[key] = rlist
			#提取结果为dic
			elif val["type"] == "dict":
				ret = self._path2array(tree,val["data"])
				result[key] = ret
		return result

	#根据tree的类型来提取，待继承
	def _picker(self,tree,sentence):
		return

	#根据具体类型初始化提取相关的对象，待继承
	def _pick(self,config):
		return 

	#外部调用
	def pick(self,config):
		ret = self._pick(config)
		if not ret:
			return ret
		if len(ret) > 1:
			return ret
		for key in ret:
			if isinstance(ret[key],list):
				return ret[key]
			return ret

######################################################  html用xpath提取的子类
class XPath(path_basic):
	def _picker(self,tree,sentence):
		return tree.xpath(sentence)

	def _pick(self,config):
		parser = etree.HTMLParser()
		tree = etree.fromstring(self.html,parser)
		#etree.dump(tree)
		return self._path2array(tree,config)

###################################################### json用路径方式提取的子类
class XJson(path_basic):
	def _picker(self,tree,sentence):
		keys = sentence.split("/")
		tmp = tree 
		for key in keys:
			if len(key) == 0:
				continue
			if not key in tmp:
				if key.isdigit() and isinstance(tmp,list) and len(tmp)>int(key):
					key = int(key)
				else:
					return False
			tmp = tmp[key]
		if isinstance(tmp,unicode) or isinstance(tmp,str):
			return [tmp]
		return tmp
	
	def _pick(self,config):
		tree = json.loads(self.html) 
		return self._path2array(tree,config)

if __name__ == "__main__":
	(header,html) = _net.Get(sys.argv[1])
	parser = etree.HTMLParser()
	tree = etree.fromstring(html,parser)
	etree.dump(tree)


################################################################# 配置示例
#xpath配置例子,解析“http://www.23us.com/html/51/51053/”
#config = {
#	"bookname":{"key":"""/html/body//h1/text()"""},	#不调用函数处理的
#	"bookname":{
#		"key":"""/html/body//h1/text()""",
#		"remake":[
#			{"method":"split","argv":[" ","0"]} #分割，取第一个
#		]
#	},
#	"author":{
#		"key":"""/html/body//h3/text()""",
#		"remake":[
#			{"method":"split","argv":["：","1"]},
#			{"method":"replace","argv":["长孙",""]}, #替换
#		]
#	},
#	"info":{ #提取字典
#		"type":"dict",
#		"data":{
#			"title":{"key":"""/html//title/text()"""},
#			"css":{
#				"key":"""/html//link/@href""",
#				"remake":[
#					{"method":"re.sub","argv":["\w*.css","test.css"]},  #使用正则替换
#				]
#			},
#			"js":{
#				"key":"""/html/head/script/@src""",
#				"not_abs_url":1,	#表示不取url的完整路径
#				"remake":[
#					{"method":"re","argv":["\w*.js"]}, #使用正则提取
#				]
#			}
#		}
#	},
#	"chapter":{  #提取列表 
#		"type":"list",
#		"block":"""/html/body//table[@id="at"]//td""",
#		"data":{
#			"name":{"key":"""./a/text()"""},
#			"url":{"key":"""./a/@href"""},
#		}
#	},
#}

#json提取示例 http://apps.wandoujia.com/api/v1/apps/com.tencent.mtt
#config = {
#	"name":{"key":"""/title"""},
#	"info":{
#		"type":"dict",
#		"data":{
#			"packageName":{"key":"""/apks/0/packageName"""},
#			"md5":{"key":"""/apks/0/md5"""},
#			"version":{
#				"key":"""/apks/0/versionName""",
#				"remake":[
#					{"method":"replace","argv":[".","_"]},
#				]
#			},
#		}
#	},
#	"chapter":{
#		"type":"list",
#		"block":"""/apks/0/securityDetail""",
#		"data":{
#			"provider":{"key":"""/provider"""},
#			"status":{"key":"""/status"""},
#			"failedInfo":{"key":"""/failedInfo"""},
#		}
#	},
#}

