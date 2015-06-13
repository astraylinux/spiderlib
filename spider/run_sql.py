#!/usr/bin/python
#coding=utf8
import os,sys
from spiderlib import sqld
import config
reload(sys)
sys.setdefaultencoding("utf-8")

					
if __name__ == "__main__":
	rs = sqld.Redis2Sql(config.g_mysql,config.g_maindb,config.g_redis,config.g_sql_queue,config.g_sql_log)
	rs.run()
