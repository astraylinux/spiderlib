#!/usr/bin/python
#coding=utf-8
import sys
sys.path.append("etc")
import sites

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
g_project_flag = "test"

#mysql
g_mysql_list = [{"host":"localhost","user":"test","pw":"123"}]
g_mysql = g_mysql_list[0]

#redis
g_redis_list = [{"host":"127.0.0.1","port":6379,"db":1}]
g_redis = g_redis_list[0]

#proxy server's ip and port info for net.py,if you need proxy
g_proxy_file = None

#the queue of the spider item data
g_newlink_queue = g_project_flag + "_newlink_queue"
g_uplink_queue = g_project_flag + "_uplink_queue"
g_pick_queue = g_project_flag + "_pick_queue"
g_data2sql_queue = g_project_flag + "_data2sql_queue"

#the queue of the sql comand in redis for run_sql.py
g_sql_queue = "mysql_queue"

#config about database
g_maindb = "test"
g_table_link = {"name":g_project_flag + "_link","division":1}
g_table_html = {"name":g_project_flag + "_html","division":1}
g_table_info = {"name":g_project_flag + "_info","division":1}

#max run threads of spider and picker
g_max_spider_thread = 3
g_max_picker_thread = 3

############### spider control ################
#if I need save html to database
#if you didn't save the html,you have to download the html again where you pick content
g_ifsave_html = False     

#spider interval config
g_default_interval = 3600*6
g_min_interval	= 3600
g_max_interval = 3600*24*7
g_rise_interval = 3600*9

#max dispatch number(new url or update url)
g_max_selectnum_new = 2000  
g_max_selectnum_up = 2000
g_max_selectnum_pick = 2000

#dispatch gap(seconds)
g_dispatch_gap = 600

############### site config ####################
g_site = sites.config
g_site_common = sites.common

############### log #########################
g_log_root		= "/root/log/"
g_dispatch_log	= g_log_root + g_project_flag + "/dispatch.log"
g_spider_log	= g_log_root + g_project_flag + "/spider.log"
g_pick_log		= g_log_root + g_project_flag + "/picker.log"
g_down_log		= g_log_root + g_project_flag + "/down.log"
g_source_log	= g_log_root + g_project_flag + "/source.log"
g_sql_log		= g_log_root + "sql.log"
