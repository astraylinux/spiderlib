#!/usr/bin/python
#coding=utf8
import sys
import config
from spiderlib import sqld
reload(sys)
sys.setdefaultencoding("utf-8")


if __name__ == "__main__":
	rs = sqld.Redis2Sql(config.G_MYSQL, config.G_MAINDB, config.G_REDIS,\
			config.G_SQL_QUEUE, config.G_SQL_LOG)
	rs.run()
