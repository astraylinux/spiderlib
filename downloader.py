#!/usr/bin/python
#coding=utf-8
import os
import sys
import threading
import time
import logging
import json
import net
import pylib
reload(sys)
sys.setdefaultencoding("utf-8")

CONFIG = None

##########################################################################
###						Process Control
##########################################################################
class DownThread(threading.Thread):
	""" 下载类，对于要下载的资源根据配置下载资源."""
	def __init__(self, num, work_as="crawl"):
		threading.Thread.__init__(self)
		self.num = num
		self.work_as = work_as
		self._redis = pylib.util.get_redis_client(CONFIG.G_REDIS)
		self._sql = pylib.sql.Sql(CONFIG.G_MYSQL,\
				CONFIG.G_MAINDB, assoc=True)
		pylib.util.log_config(CONFIG.G_DOWN_LOG)

	def _data2redis_sql(self, data, table_cfg, op_type):
		""" Sql语句放到redis队列，由sqld来执行."""
		table = table_cfg["name"]
		division = table_cfg["division"]
		pylib.sql.data2redis(data, self._redis, CONFIG.g_sql_queue, \
				table, op_type, "md5", division)

	def _state(self, md5, state, table_cfg):
		""" 更新状态."""
		self._data2redis_sql({"md5":md5, "state":state}, table_cfg, "update")
		#self._data2redis_sql(data, table_cfg, "update")

	def _download(self, task_data):
		""" 下载流程."""
		url = task_data["down_url"].replace(" ", "%20")
		md5 = task_data["md5"]
		domain = url.split("/")[2]
		d_config = CONFIG.g_site[domain]
		down_config = d_config["down"]
		table_cfg = down_config["down_table"]

		local_dir = down_config["down_dir"] + md5[-2:] + "/"
		if not os.path.exists(local_dir):
			os.mkdir(local_dir)

		#决定下载后文件的后缀名
		suf = url.split(".")[-1]
		if (suf in "php js html shtml" or len(suf) > 5) and \
				"default_suf" in down_config:
			suf = down_config["default_suf"]

		path = local_dir + md5 + "." + suf
		print url, path
		if pylib.net.download_file(url, path, timeout=120):
			save_path = path.replace(down_config["down_dir"], "/")
			data = {"md5":md5, "path":save_path, "state":CONFIG.G_STATE_DOWNED}
			self._data2redis_sql(data, table_cfg, "update")
			return (CONFIG.G_STATE_DOWNED, 1)
		else:
			data = {"md5":md5, "state":CONFIG.G_STATE_ERROR}
			self._data2redis_sql(data, table_cfg, "update")
		return (CONFIG.G_STATE_ERROR, 0)

	def run(self):
		while True:
			url = ""
			try:
				item = self._redis.rpop(CONFIG.g_down_queue)
				if not item:
					time.sleep(5)
					continue
				task_data = json.loads(item)
				(state, count) = self._download(task_data)

				md5 = task_data["md5"]
				url = task_data["down_url"]
				if not url:
					continue
				if count != 0 or state == CONFIG.G_STATE_ERROR:
					logging.info("[DownOk]:%s", md5)
				else:
					logging.info("[DownFail]:%s %s", md5, url)
			except Exception, msg:
				logging.exception("[DownFail]:[except] " + url)
				logging.exception("[DownFail]:[except] " + str(msg))
				if "MySQL" in str(msg):
					self._sql.check_connect()

#==============================================================
#if __name__ == "__main__":
#	if len(sys.argv) > 1:
#		url = "http://www.isijie.net/wp-content/uploads/2015/04/15/229.jpg"
#		if len(sys.argv) > 2:
#			url = sys.argv[2]
#		if sys.argv[1] == "test":
#			thread = downThread(0, "test")
#		else:
#			thread = downThread(0)
#		data = {"down_url":url}
#		data["md5"] = pylib.util.GetMd5(url)
#		print thread._download(data)
#	else:
#		for index in range(0, CONFIG.g_max_down_thread):
#			thread = downThread(index)
#			thread.start()
#			time.sleep(1)
