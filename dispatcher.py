#!/usr/bin/python
#coding=utf8
import sys
import pylib
import time
import json
import logging
reload(sys)
sys.setdefaultencoding("utf-8")

CONFIG = None

class Dispatcher(object):
	"""
		A controller who get datas from mysql, and put them into redis queue,
		other worker will get task from redis, and execute.
	"""
	def __init__(self):
		""" Init the logging, connect to redis and mysql."""
		pylib.util.log_config(CONFIG.G_DISPATCH_LOG)
		self._redis = pylib.util.get_redis_client(CONFIG.G_REDIS)
		self._sql = pylib.sql.Sql(CONFIG.G_MYSQL, CONFIG.G_MAINDB, assoc=True)

	def get_new_url(self):
		""" Get urls that never be visit insert into redis queue."""
		where = "where crawl_state=%s limit %s"%(CONFIG.G_STATUS_UNCRAWLED,\
				CONFIG.G_MAX_SELECTNUM_NEW)
		rows = self._sql.select(CONFIG.G_TABLE_LINK, ["*"], where)
		for row in rows:
			data = json.dumps(row)
			self._redis.lpush(CONFIG.G_NEW_LINK_QUEUE, data)
		if len(rows) > 0:
			logging.info("new links :%s", len(rows))

	def get_update_url(self):
		""" Get urls that need visit again. Insert into redis queue."""
		where = "where ((CEIL(un_uptimes-uptimes)+1)*%s+last_time)<%s \
				and crawl_state=%s limit %s"%(CONFIG.g_rise_linterval, \
				int(time.time()), CONFIG.G_STATUS_CRAWLED, \
				CONFIG.g_max_selectnum_up)
		rows = self._sql.select(CONFIG.G_TABLE_LINK, ["*"], where)
		for row in rows:
			data = json.dumps(row)
			self._redis.lpush(CONFIG.G_UPDATE_QUEUE, data)
		if len(rows) > 0:
			logging.info("up links :%s", len(rows))

	def get_pick_url(self):
		""" Get urls that the html will be pick."""
		table = CONFIG.G_TABLE_LINK
		p_type = CONFIG.G_SITE_COMMON.G_PAGETYPE["detail"]["type"]
		where = "where type=%s and pick_state in (%s, %s) limit %s"%(\
				p_type, CONFIG.G_STATE_UNPICK, CONFIG.G_STATE_UPDATE,\
				CONFIG.G_MAX_SELECTNUM_PICK)

		result = []
		for i in range(0, table["division"]):
			if table["division"] == 1:
				rows = self._sql.select(table["name"], ["*"], where)
				result = rows
			else:
				rows = self._sql.select(table["name"] + str(i),\
						["*"], where)
				for row in rows:
					result.append(row)

		for row in result:
			data = json.dumps(row)
			self._redis.rpush(CONFIG.G_PICK_QUEUE, data)
		if len(result) > 0:
			logging.info("up  pick:%s", len(rows))

	def run(self):
		""" Start Dispatcher."""
		while True:
			self._sql.check_connect()
			if self._redis.llen(CONFIG.G_NEW_LINK_QUEUE) == 0:
				self.get_new_url()

			if self._redis.llen(CONFIG.G_UPDATE_QUEUE) == 0:
				self.get_update_url()

			if self._redis.llen(CONFIG.g_pick_queue) == 0:
				self.get_pick_url()

			time.sleep(CONFIG.G_DESPATCH_GAP)
