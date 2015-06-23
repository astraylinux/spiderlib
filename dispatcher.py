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
		gdc = CONFIG.G_DISPATCH_CRAWLER
		id_limit = "id%%%d=%d and "%(gdc[1], gdc[0])
		if CONFIG.G_INTO_DETAIL:
			where = "where %s crawl_state=%s limit %s"%(id_limit,\
				CONFIG.G_STATUS_UNCRAWLED, CONFIG.G_MAX_SELECTNUM_NEW)
		else:
			where = "where %s crawl_state=%s and not type=1 limit %s"%(\
				id_limit, CONFIG.G_STATUS_UNCRAWLED, CONFIG.G_MAX_SELECTNUM_NEW)
		rows = self._sql.select(CONFIG.G_TABLE_LINK["name"], ["*"], where)
		for row in rows:
			data = json.dumps(row)
			self._redis.lpush(CONFIG.G_NEW_LINK_QUEUE, data)
		if len(rows) > 0:
			logging.info("new links :%s", len(rows))

	def get_update_url(self):
		""" Get urls that need visit again. Insert into redis queue."""
		gdc = CONFIG.G_DISPATCH_CRAWLER
		id_limit = "id%%%d=%d and "%(gdc[1], gdc[0])
		where = "where %s ((CEIL(un_uptimes-uptimes)+1)*%s+last_time)<%s\
				and crawl_state=%s limit %s"%(id_limit, \
				CONFIG.G_RISE_INTERVAL, int(time.time()),\
				CONFIG.G_STATUS_CRAWLED, CONFIG.G_MAX_SELECTNUM_UP)
		rows = self._sql.select(CONFIG.G_TABLE_LINK["name"], ["*"], where)
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
				rows = self._sql.select(table["name"] + \
						str(pylib.util.dec2hex(i)), ["*"], where)
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
			try:
				self._sql.check_connect()
				if self._redis.llen(CONFIG.G_NEW_LINK_QUEUE) == 0:
					self.get_new_url()

				if self._redis.llen(CONFIG.G_UPDATE_QUEUE) == 0:
					self.get_update_url()

				if self._redis.llen(CONFIG.G_PICK_QUEUE) == 0:
					self.get_pick_url()

				time.sleep(CONFIG.G_DISPATCH_GAP)
			except Exception, msg:
				if "MySQL" in str(msg):
					continue

