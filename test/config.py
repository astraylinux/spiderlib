#!/usr/bin/python
#coding=utf-8
import etc

######### define state ###########
#define som states for crawl
G_STATUS_UNCRAWLED = 0
G_STATUS_CRAWLED = 1
G_STATUS_ERROR = -1

#define some states for pick and download
G_STATE_UNPICK = 0
G_STATE_PICKED = 1
G_STATE_UPDATE = 2
G_STATE_ERROR = -1
G_STATE_NET_ERROR = -2

#############  server config ####################
#project flag, it use as a prefix in table name or as a root directory name of log
G_PROJECT_FLAG = "ask"

#mysql
G_MYSQL_LIST = [{"host":"127.0.0.1", "user":"test", "pw":"123"}]
G_MYSQL = G_MYSQL_LIST[0]

#redis
G_REDIS_LIST = [{"host":"127.0.0.1", "port":6379, "db":0}]
G_REDIS = G_REDIS_LIST[0]

#proxy server's ip and port info for net.py,if you need proxy
G_PROXY_FILE = None

#the queue of the spider item data
G_NEW_LINK_QUEUE = G_PROJECT_FLAG + "_newlink_queue"
G_UPDATE_QUEUE = G_PROJECT_FLAG + "_uplink_queue"
G_PICK_QUEUE = G_PROJECT_FLAG + "_pick_queue"
G_DATA2SQL_QUEUE = G_PROJECT_FLAG + "_data2sql_queue"

#the queue of the sql comand in redis for run_sql.py
G_SQL_QUEUE = "mysql_queue"

#config about database
#division could be 1, 16, 256, the 16 use md5 last char
#256 use the md5 last two char
G_MAINDB = "test"
G_TABLE_LINK = {"name":G_PROJECT_FLAG + "_link", "division":1}
G_TABLE_HTML = {"name":G_PROJECT_FLAG + "_html", "division":1}
G_TABLE_INFO = {"name":G_PROJECT_FLAG + "_info", "division":1}

#max run threads of spider and picker
G_MAX_SPIDER_THREAD = 3
G_MAX_PICKER_THREAD = 1

############### spider control ################
#if I need save html to database
#if you didn't save the html,you have to download
#the html again where you pick content
G_IFSAVE_HTML = True
#if G_IFSAVE_HTML=True and this is ture
#will save the process html(not detail page)
G_IFSAVE_PASS = False
#if this not True, crawler will not look for new link's from detail page
G_INTO_DETAIL = False

#spider interval config
G_DEFAULT_INTERVAL = 3600*6
G_MIN_INTERVAL	= 3600
G_MAX_INTERVAL = 3600*24*7
G_RISE_INTERVAL = 3600*9

#max dispatch number(new url or update url)
G_MAX_SELECTNUM_NEW = 2000
G_MAX_SELECTNUM_UP = 2000
G_MAX_SELECTNUM_PICK = 2000

#crawler only dispatch the task which id%3 == 1
G_DISPATCH_CRAWLER = (1, 3)
#dispatch gap(seconds)
G_DISPATCH_GAP = 10

############### site config ####################
G_SITE = etc.webset.SITES
G_SITE_COMMON = etc.common

############### log #########################
G_LOG_ROOT = "/home/astray/git/log/"
G_DISPATCH_LOG = G_LOG_ROOT + G_PROJECT_FLAG + "/dispatch.log"
G_SPIDER_LOG = G_LOG_ROOT + G_PROJECT_FLAG + "/spider.log"
G_PICK_LOG = G_LOG_ROOT + G_PROJECT_FLAG + "/picker.log"
G_DOWN_LOG = G_LOG_ROOT + G_PROJECT_FLAG + "/down.log"
G_SOURCE_LOG = G_LOG_ROOT + G_PROJECT_FLAG + "/source.log"
G_SQL_LOG = G_LOG_ROOT + "sql.log"
