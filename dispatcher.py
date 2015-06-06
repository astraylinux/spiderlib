#!/usr/bin/python
#coding=utf8
import os,sys
import tb
import time
import config
import net
import redis
import json
import logging
reload(sys)
sys.setdefaultencoding("utf-8")

class dispatcher:
	def __init__(self):
		tb.util.LogConfig(config.g_dispatch_log)
	
	def run(self):
		while True:
			rc = tb.util.GetRedisClient(config.g_redis)
			cursor = tb.sql.GetCursor(config.g_mysql,config.g_maindb,True)

			############  new url queue
			if rc.llen(config.g_newlink_queue) == 0:
				where = "crawl_state=%s limit %s"%(config.G_STATUS_UNCRAWLED,config.g_max_selectnum_new)
				rows = tb.sql.ExeSelect(cursor,config.g_table_link,["*"],where)
				for row in rows:
					data = json.dumps(row,ensure_ascii=False)
					rc.lpush(config.g_newlink_queue,data)
				if len(rows) > 0:
					logging.info("new links :%s"%(len(rows)))

			############# update queue
			if rc.llen(config.g_uplink_queue) == 0:
				where = "((CEIL(un_uptimes-uptimes)+1)*%s+last_time)<%s and crawl_state=%s limit %s"%(config.g_rise_linterval,int(time.time()),config.G_STATUS_CRAWLED,config.g_max_selectnum_up)
				rows = tb.sql.ExeSelect(cursor,config.g_table_link,["*"],where)
				for row in rows:
					data = json.dumps(row,ensure_ascii=False)
					rc.lpush(config.g_uplink_queue,data)
				if len(rows) > 0:
					logging.info("up  links :%s"%(len(rows)))

			############# pick queue
			if rc.llen(config.g_pick_queue) == 0:
				table = config.g_table_link
				p_type = config.g_site_common.G_PAGETYPE["detail"]["type"]
				where = "type=%s and pick_state in (%s,%s) limit %s"%(p_type,config.G_STATE_UNPICK,config.G_STATE_UPDATE,config.g_max_selectnum_pick)
				result = []
				for i in range(0,table["division"]):
					if table["division"] == 1:
						rows = tb.sql.ExeSelect(cursor,table["name"],["*"],where)
						result = rows
					else:
						rows = tb.sql.ExeSelect(cursor,table["name"]+str(i),["*"],where)
						for row in rows:
							result.append(row)
				for row in result:
					data = json.dumps(row,ensure_ascii=False)
					rc.rpush(config.g_pick_queue,data)
				if len(result) > 0:
					logging.info("up  pick:%s"%(len(rows)))
			
			time.sleep(8)#config.g_dispatch_gap)


if __name__ == "__main__":
	dp = dispatcher()	
	dp.run()
