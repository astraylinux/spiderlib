#!/usr/bin/python
#coding=utf-8
""" Filename: picker.py """
import sys
import threading
import time
import logging
import json
import net
from pylib import util, sql, expath
reload(sys)
sys.setdefaultencoding("utf-8")

CONFIG = None

def check_must_key(p_config, ret):
	for key in p_config["must_key"]:
		if not ret[key]:
			return False
	return True

def print_for_test(ret):
	print "#"*30
	if isinstance(ret, list):
		for items in ret:
			print "="*20
			for key, val in items.items():
				print key, val
	elif isinstance(ret, dict):
		for key, val in ret.items():
			print key, val

###################################################################################
###						Process Control
###################################################################################
class Picker(threading.Thread):
	def __init__(self, num, workas="crawl"):
		threading.Thread.__init__(self)
		self._num = num
		self._workas = workas
		self._redis = util.get_redis_client(CONFIG.G_REDIS)
		self._sql = sql.Sql(CONFIG.G_MYSQL, CONFIG.G_MAINDB, assoc=True)
		util.log_config(CONFIG.G_PICK_LOG)

	def _db_had(self, check_list, table_cfg):
		self._sql.check_connect()
		table = table_cfg["name"]
		division = table_cfg["division"]
		if division == 16 or division == 256:
			ret_dict = {}
			list_dict = {}
			for md5 in check_list:
				flag = md5[-1:] if division == 16 else md5[-2:]
				if flag in list_dict:
					list_dict[flag].append(md5)
				else:
					list_dict[flag] = [md5]
			for key in list_dict:
				has = self._sql.exist(table + key, list_dict[key], "md5")
				ret_dict.update(has)
			return ret_dict
		else:
			return self._sql.exist(table, check_list, "md5")

	def _data2redis_sql(self, sqldata, table_cfg, op_type):
		table = table_cfg["name"]
		division = table_cfg["division"]
		sql.data2redis(sqldata, self._redis, CONFIG.G_SQL_QUEUE, \
				table, op_type, "md5", division)

	def _pick_state(self, md5, state, table_cfg):
		self._data2redis_sql({"md5":md5, "pick_state":state}, table_cfg, "update")


	def _deal_pick_ret(self, ret, url, md5, table_cfg):
		#查内容是否在库里，根据情况执行插入或更新
		ret_count = 0
		insert_count = 0
		update_count = 0
		if isinstance(ret, list):
			#提取结果是队列的情况
			ret_count = len(ret)
			check_list = []
			for i in range(0, len(ret)):
				ret[i]["md5"] = util.md5(ret[i]["url"])
				check_list.append(ret[i]["md5"])
			check_ret = self._db_had(check_list, table_cfg)
			for data in ret:
				if data["md5"] in check_ret and self._workas == "update":
					self._data2redis_sql(data, table_cfg, "update")
					update_count += 1
				else:
					self._data2redis_sql(data, table_cfg, "insert")
					insert_count += 1
		elif isinstance(ret, dict):
			#提取结果是字典的情况
			ret_count = 1
			ret["url"] = url
			ret["md5"] = md5
			if self._db_had({"md5":md5}, table_cfg):
				if self._workas == "update":
					self._data2redis_sql(ret, table_cfg, "update")
					update_count += 1
			else:
				self._data2redis_sql(ret, table_cfg, "insert")
				insert_count += 1
		if ret:
			self._pick_state(md5, CONFIG.G_STATE_PICKED, CONFIG.G_TABLE_LINK)
		if self._workas == "update":
			return (update_count, ret_count)
		else:
			return (insert_count, ret_count)

	def _pick(self, d_config, html, task_data):
		md5 = task_data["md5"]
		url = task_data["url"]
		page_type = task_data["type"]

		#根据xpath配置提取html里的信息
		p_config = d_config["picker"][page_type]
		table_cfg = p_config["table"]
		picker = expath.XPath(url, html, d_config["default_code"])
		xpath_config = p_config["path"]
		ret = picker.pick(xpath_config)

		#检查必需有值的字段是否有值
		if not check_must_key(p_config, ret):
			self._pick_state(md5, CONFIG.G_STATE_ERROR, CONFIG.G_TABLE_LINK)
			return (0, 0)

		if self._workas == "test":
			print_for_test(ret)
			return	(0, len(ret))

		return self._deal_pick_ret(ret, url, md5, table_cfg)


	def _run(self, task_data):
		url = task_data["url"]
		domain = url.split("/")[2]
		d_config = CONFIG.G_SITE[domain]

		(header, html) = net.get(url)
		if header["code"] == 200:
			count = self._pick(d_config, html, task_data)
			return (CONFIG.G_STATE_PICKED, count)

		self._pick_state(task_data["md5"], CONFIG.G_STATE_ERROR,\
				CONFIG.G_TABLE_LINK)
		return (CONFIG.G_STATE_NET_ERROR, (0, 0))

	def run(self):
		while True:
			url = ""
			try:
				item = self._redis.rpop(CONFIG.G_PICK_QUEUE)
				if not item:
					time.sleep(5)
					continue
				task_data = json.loads(item)
				(state, count) = self._run(task_data)

				md5 = task_data["md5"]
				url = task_data["url"]
				if count[1] != 0:
					logging.info("[PickOk][%d][%d]:%s %s", \
							count[0], count[1], md5, url)
				else:
					logging.info("[PickFail]: %d ", state + url)
			except Exception, msg:
				logging.exception("[PickFail]:[except] " + url)
				logging.exception("[PickFail]:[except] " + str(msg))
				if "MySQL" in str(msg):
					self._sql.check_connect()

#==============================================================
#if __name__ == "__main__":
#	if len(sys.argv) > 1:
#		if sys.argv[1] == "test":
#			thread = Picker(0, "test")
#		else:
#			thread = Picker(0)
#		data = {"url":"http://manhua.dmzj.com/yaojingdeweiba/"}
#		data["md5"] = util.GetMd5(data["url"])
#		data["type"] = 1
#		print thread._run(data)
#	else:
#		for index in range(0, CONFIG.g_max_picker_thread):
#			thread = pickThread(index)
#			thread.start()
#			time.sleep(1)
