""" Filename: picker.py """
#!/usr/bin/python
#coding=utf-8
import sys
import threading
import time
import logging
import json
import tb
import config
import net
reload(sys)
sys.setdefaultencoding("utf-8")

tb.util.LogConfig(config.g_pick_log)
###################################################################################
###						Process Control 
###################################################################################
class pickThread(threading.Thread):
	def __init__(self,num,work_as="crawl"):
		threading.Thread.__init__(self)
		self.num = num
		self.work_as = work_as
		self.rc = tb.util.GetRedisClient(config.g_redis)
		self.cursor = tb.sql.GetCursor(config.g_mysql,config.g_maindb,dict=True)			

	def _is_connect(self):
		self.cursor = tb.sql.is_connect(self.cursor,config.g_mysql,config.g_maindb,dict=True)
	
	#检查是否在数据库里，返回md5队列
	def _db_had(self,check_list,table_cfg):
		self._is_connect()
		table = table_cfg["name"]
		division = table_cfg["division"]
		return tb.sql.isInDatabase(self.cursor,table,check_list,division,"md5")

	def _data2redis_sql(self,data,table_cfg,op_type):
		table = table_cfg["name"]
		division = table_cfg["division"]
		tb.sql.data2redis(data,self.rc,config.g_sql_queue,table,op_type,"md5",division)

	def _pick_state(self,md5,state,table_cfg):
		self._data2redis_sql({"md5":md5,"pick_state":state},table_cfg,"update")

	#调试时用来打印结果信息
	def _print_for_test(self,ret):
		print "#"*30
		if isinstance(ret,list):
			for items in ret:
				print "="*20
				for key,val in items.items():
					print key,val
		elif isinstance(ret,dict):
			for key,val in ret.items():
				print key,val
		
	def _check_must_key(self,p_config,ret):
		for key in p_config["must_key"]:
			if not ret[key]:
				return False
		return True	

	def _pick(self,d_config,html,task_data):
		md5 = task_data["md5"]
		url = task_data["url"]
		type = task_data["type"]

		#根据xpath配置提取html里的信息
		p_config = d_config.picker[type]
		table_cfg = p_config["table"]
		picker = tb.expath.XPath(url,html,d_config.default_code)
		xpath_config = p_config["path"] 
		ret = picker.pick(xpath_config)

		#检查必需有值的字段是否有值
		if not self._check_must_key(p_config,ret):
			self._pick_state(md5,config.G_STATE_ERROR,config.g_table_link)
			return (0,0)

		#检查内容是否在库，根据情况执行插入或更新
		ret_count = 0
		insert_count = 0
		update_count = 0
		if self.work_as == "test":
			self._print_for_test(ret)
			return	(0,len(ret))

		if isinstance(ret,list):
			#提取结果是队列的情况
			ret_count = len(ret)
			check_list = []
			for i in range(0,len(ret)):
				ret[i]["md5"] = tb.util.GetMd5(ret[i]["url"])
				check_list.append({"md5":ret[i]["md5"]})
			check_ret = self._db_had(check_list,table_cfg)
			for data in ret:
				if data["md5"] in check_list:
					if self.work_as == "update":
						self._data2redis_sql(data,table_cfg,"update")
						update_count += 1
				else:
					self._data2redis_sql(data,table_cfg,"insert")
					insert_count += 1
		elif isinstance(ret,dict):	
			#提取结果是字典的情况
			ret_count = 1
			ret["url"] = url
			ret["md5"] = md5
			if self._db_had({"md5":md5},table_cfg):
				if self.work_as == "update":
					self._data2redis_sql(ret,table_cfg,"update")
					update_count += 1
			else:
				self._data2redis_sql(ret,table_cfg,"insert")
				insert_count += 1
		if ret:
			self._pick_state(md5,config.G_STATE_PICKED,config.g_table_link)
		if self.work_as == "update":
			return (update_count,ret_count)
		else:
			return (insert_count,ret_count)

	def _run(self,task_data):
		url = task_data["url"]
		domain = url.split("/")[2]
		d_config = config.g_site[domain]

		(header,html) = net.Get(url)
		if header["code"] == 200:
			count = self._pick(d_config,html,task_data)	
			return (config.G_STATE_PICKED,count)

		self._pick_state(task_data["md5"],config.G_STATE_ERROR,config.g_table_link)
		return (config.G_STATE_NET_ERROR,(0,0)) 
	
	def run(self):
		while True:
			url = ""
			try:
				item = self.rc.rpop(config.g_pick_queue)
				if not item:
					time.sleep(5)
					continue
				task_data = json.loads(item)
				(state,count) = self._run(task_data)	

				md5 = task_data["md5"]
				url = task_data["url"]
				if count[1] != 0:
					logging.info("[PickOk][%d][%d]:%s %s"%(count[0],count[1],md5,url))
				else:
					logging.info("[PickFail]: %d "%(state) + url)
			except Exception,e:
				logging.exception("[PickFail]:[except] " + url)
				logging.exception("[PickFail]:[except] " + str(e))
				if "MySQL" in str(e):
					self.cursor.close()
					self.cursor = tb.sql.GetCursor(config.g_mysql,config.g_maindb,dict=True)			

#==============================================================
if __name__ == "__main__":
	if len(sys.argv) > 1:
		if sys.argv[1] == "test":
			thread = pickThread(0,"test")
		else:
			thread = pickThread(0)
		data = {"url":"http://manhua.dmzj.com/yaojingdeweiba/"}
		data["md5"] = tb.util.GetMd5(data["url"])
		data["type"] = 1
		print thread._run(data)
	else:
		for index in range(0,config.g_max_picker_thread):
			thread = pickThread(index)
			thread.start()
			time.sleep(1)
