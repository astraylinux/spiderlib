#!/usr/bin/python
#coding=utf8
import sys
import time
import json
import logging
from pylib import sql, util
reload(sys)
sys.setdefaultencoding("utf-8")


class Redis2Sql(object):
	def __init__(self, mysql, mysql_db, rserver, queue, log):
		self._db	= mysql_db
		self._redis = rserver
		self._queue = queue
		self._sql = sql.Sql(mysql, mysql_db)
		self._redis = util.get_redis_client(rserver)
		util.log_config(log)

	def _result2sql(self, result):
		insert_count = 0
		update_count = 0
		for key, val in result.items():
			pieces = key.split("@@")
			if pieces[0] == "insert":
				insert_count += self._sql.insert(pieces[1], val)
			elif pieces[0] == "update":
				for data in val:
					#time.sleep(0.02)
					where = {data["key"]:data["data"][data["key"]]}
					update_count += self._sql.update(pieces[1],\
							data["data"], where)
		return (insert_count, update_count)

	def _pre_analysis(self, jset):
		result = {}
		for key, value in jset["data"].items():
			if isinstance(value, list) or isinstance(value, dict):
				jset["data"][key] = json.dumps(value, ensure_ascii=False)

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
		return (key, result)


	def data2db(self, result, ptime):
		start = time.time()
		self._sql.check_connect()
		(insert_count, update_count) = self._result2sql(result)
		stime = time.time() - start

		if insert_count > 0 or update_count > 0:
			logging.info("insert=%d update=%d time:pre=%-0.4f sql=%-0.4f",\
					insert_count, update_count, ptime, stime)
		if self._redis.llen(self._queue) > 0:
			time.sleep(0.1)

	def run(self):
		while True:
			try:
				duplicate = {}
				start = time.time()
				result = {}

				#get data from _redis and use _pre_analysis to deal them
				while self._redis.llen(self._queue) > 0:
					ret = self._redis.rpop(self._queue)
					if ret in duplicate:
						continue
					duplicate[ret] = 1
					jset = json.loads(ret)
					(key, result) = self._pre_analysis(jset)
					if len(result[key]) >= 100:
						return
				ptime = time.time() - start
				self.data2db(result, ptime)
			except Exception, msg:
				logging.exception(str(msg))
			time.sleep(2)
