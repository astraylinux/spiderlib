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
		self._batch = {}
		util.log_config(log)

	def _result2sql(self):
		insert_count = 0
		update_count = 0
		for key, val in self._batch.items():
			pieces = key.split("@@")
			if pieces[0] == "insert":
				insert_count += self._sql.insert(pieces[1], val)
			elif pieces[0] == "update":
				for data in val:
					#time.sleep(0.02)
					where = {data["key"]:data["data"][data["key"]]}
					update_count += self._sql.update(pieces[1],\
							data["data"], where)
		self._sql.commit()
		return (insert_count, update_count)

	def _batch_length(self):
		count = 0
		for asort in self._batch.items():
			count += len(asort[1])
		return count

	def _pre_analysis(self, jset):
		for key, value in jset["data"].items():
			if isinstance(value, list) or isinstance(value, dict):
				jset["data"][key] = json.dumps(value, ensure_ascii=False)

		key = jset["type"] + "@@" + jset["table"]
		if jset["type"] == "insert":
			if not key in self._batch:
				self._batch[key] = [jset["data"]]
			else:
				self._batch[key].append(jset["data"])
		elif jset["type"] == "update":
			if not key in self._batch:
				self._batch[key] = [jset]
			else:
				self._batch[key].append(jset)

	def data2db(self, ptime):
		start = time.time()
		self._sql.check_connect()
		(insert_count, update_count) = self._result2sql()
		stime = time.time() - start

		if insert_count > 0 or update_count > 0:
			logging.info("insert=%d update=%d time:pre=%-0.4f sql=%-0.4f",\
					insert_count, update_count, ptime, stime)
		if self._redis.llen(self._queue) > 0:
			time.sleep(0.1)

	def run(self):
		while True:
			if self._redis.llen(self._queue) == 0:
				time.sleep(2)
			try:
				start = time.time()
				self._batch = {}

				#get data from _redis and use _pre_analysis to deal them
				while self._redis.llen(self._queue) > 0:
					ret = self._redis.rpop(self._queue)
					jset = json.loads(ret)
					self._pre_analysis(jset)
					if self._batch_length() >= 100:
						break
				ptime = time.time() - start
				if self._batch:
					self.data2db(ptime)
			except Exception, msg:
				logging.exception(str(msg))
