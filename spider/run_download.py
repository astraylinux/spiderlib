#!/usr/bin/python
#coding=utf-8
import sys,os
import threading
import time
import logging
import json
import tb
import config
import net
import urllib
reload(sys)
sys.setdefaultencoding("utf-8")

tb.util.LogConfig(config.g_down_log)
###################################################################################
###						Process Control 
###################################################################################
class downThread(threading.Thread):
	def __init__(self,num,work_as="crawl"):
		threading.Thread.__init__(self)
		self.num = num
		self.work_as = work_as
		self.rc = tb.util.GetRedisClient(config.g_redis)
		self.cursor = tb.sql.GetCursor(config.g_mysql,config.g_maindb,dict=True)			

	def _is_connect(self):
		self.cursor = tb.sql.is_connect(self.cursor,config.g_mysql,config.g_maindb,dict=True)

	def _data2redis_sql(self,data,table_cfg,op_type):
		table = table_cfg["name"]
		division = table_cfg["division"]
		tb.sql.data2redis(data,self.rc,config.g_sql_queue,table,op_type,"md5",division)

	def _state(self,md5,state,table_cfg):
		self._data2redis_sql({"md5":md5,"state":state},table_cfg,"update")
		#self._data2redis_sql(data,table_cfg,"update")

	def _run(self,task_data):
		url = task_data["down_url"].replace(" ","%20")
		md5 = task_data["md5"]
		domain = url.split("/")[2]
		d_config = config.g_site[domain]
		down_config = d_config.down_config 
		table_cfg = down_config["down_table"]

		local_dir = down_config["down_dir"] + md5[-2:] + "/"
		if not os.path.exists(local_dir):
			os.mkdir(local_dir)

		suf = url.split(".")[-1]
		if (suf in "php js html shtml" or len(suf) >5) and "default_suf" in down_config:
			suf = down_config["default_suf"]
		path = local_dir + md5 + "." + suf 
		print url,path
		if tb.net.DownloadFile(url, path,timeout=120):
			save_path = path.replace(down_config["down_dir"],"/")
			data = {"md5":md5,"path":save_path,"state":config.G_STATE_DOWNED}
			self._data2redis_sql(data,table_cfg,"update")
			return (config.G_STATE_DOWNED,1)
		else:
			data = {"md5":md5,"state":config.G_STATE_ERROR}
			self._data2redis_sql(data,table_cfg,"update")
		return (config.G_STATE_ERROR,0) 
	
	def run(self):
		while True:
			url = ""
			try:
				item = self.rc.rpop(config.g_down_queue)
				if not item:
					time.sleep(5)
					continue
				task_data = json.loads(item)
				(state,count) = self._run(task_data)	

				md5 = task_data["md5"]
				url = task_data["down_url"]
				if not url:
					continue
				if count != 0:
					logging.info("[DownOk]:%s"%(md5))
				else:
					logging.info("[DownFail]:%s %s"%(md5,url))
			except Exception,e:
				logging.exception("[DownFail]:[except] " + url)
				logging.exception("[DownFail]:[except] " + str(e))
				if "MySQL" in str(e):
					self.cursor.close()
					self.cursor = tb.sql.GetCursor(config.g_mysql,config.g_maindb,dict=True)			

#==============================================================
if __name__ == "__main__":
	if len(sys.argv) > 1:
		url = "http://www.isijie.net/wp-content/uploads/2015/04/15/229.jpg"
		if len(sys.argv) > 2:
			url = sys.argv[2]
		if sys.argv[1] == "test":
			thread = downThread(0,"test")
		else:
			thread = downThread(0)
		data = {"down_url":url}
		data["md5"] = tb.util.GetMd5(url)
		print thread._run(data)
	else:
		for index in range(0,config.g_max_down_thread):
			thread = downThread(index)
			thread.start()
			time.sleep(1)
