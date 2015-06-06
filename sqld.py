#!/usr/bin/python
#coding=utf8
import os,sys
from SimplePythonLib import sql,util
import time
import socket
import sys
import json
import logging
reload(sys)
sys.setdefaultencoding("utf-8")

class Redis2Sql:
	def __init__(self,mysql,db,rserver,queue,log):
		self.mysql= mysql
		self.db	= db
		self.redis = rserver
		self.queue = queue
		self.cursor = sql.GetCursor(mysql,db)
		self.rc = util.GetRedisClient(rserver)
		util.LogConfig(log)

	def _check_connect(self):
		self.cursor = sql.is_connect(self.cursor,self.mysql,self.db)

	def _result2sql(self,result):
		insert_count = 0
		update_count = 0
		for key,val in result.items():
			sp = key.split("@@")
			if sp[0] == "insert":
				insert_count += sql.ExeInsert(self.cursor,sp[1],val)
			elif sp[0] == "update":
				for data in val:
					#time.sleep(0.02)
					where = {data["key"]:data["data"][data["key"]]}
					update_count += sql.ExeUpdate(self.cursor,sp[1],data["data"],where)
		return (insert_count,update_count)

	def _pre_analysis(self,jset):
		result = {} 
		for k,v in jset["data"].items():
			if isinstance(v,list) or isinstance(v,dict):
				jset["data"][k] = json.dumps(v,ensure_ascii=False)
				
		key = jset["type"] + "@@" + jset["table"]
		if jset["type"] == "insert":
			if not key in result:
				result[key] = [jset["data"]]
			else:
				result[key].append(jset["data"])
		elif jset["type"] == "update":
			if not key in result:
				result[key] = [jset]
			else:
				result[key].append(jset)
		if len(result[key]) >= 100:
			break

	def _run(self):
		duplicate = {}
		count = 0
		start = time.time()
		result = {}

		#get data from redis and use _pre_analysis to deal them
		while self.rc.llen(self.queue) > 0:
			ret = self.rc.rpop(self.queue)
			if ret in duplicate:
				continue
			duplicate[ret] = 1
			jset = json.loads(ret)
			result = self._pre_analysis(jset)
		ptime = time.time() - start

		start = time.time()
		self._check_connect()
		(insert_count,update_count) = self._result2sql(result)
		stime = time.time() - start

		if insert_count>0 or update_count>0:
			logging.info("insert=%d update=%d time:pre=%-0.4f sql=%-0.4f"%(insert_count,update_count,ptime,stime))
		if self.rc.llen(self.queue) > 0:
			time.sleep(0.1)
			continue
	
	def run(self):
		while True:	
			try:
				self._run()
			except Exception,e:
				logging.exception(str(e))
			time.sleep(2)
