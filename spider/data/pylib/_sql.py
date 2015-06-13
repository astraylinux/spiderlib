#!/usr/bin/python
#coding=utf-8
import sys
#import pymssql
import json
import redis
import MySQLdb
import MySQLdb.cursors
import datetime
reload(sys)
sys.setdefaultencoding("utf-8")

#========================================= init sql
def GetCursor(server,db,dict=False,type=0):
	_host = server["host"]
	_user = server["user"]
	_pw = server["pw"]
	cursor = None
	if type == 0: #mysql 
		conn = None
		if dict:
			conn = MySQLdb.connect(_host,_user,_pw,db,3306,cursorclass=MySQLdb.cursors.DictCursor)
		else:
			conn = MySQLdb.connect(_host,_user,_pw,db,3306)
		cursor = conn.cursor()
		cursor.execute("set names utf8")
	if type == 1: #sql server
		conn = pymssql.connect(host=_host,user=_user,database=db,password=_pw,charset="utf8")
		cursor = conn.cursor()
	return cursor

def is_connect(cursor,server,db,dict=False):
	try:
		cursor.connection.ping()
		return cursor 
	except Exception,e:
		cursor.close()
		cursor = GetCursor(server,db,dict)
		return cursor 

def trans2str(input):
	output=input
	if isinstance(input, datetime.date):
		try:
			output=input.strftime( '%Y-%m-%d %H:%M:%S' )
		except:
			output="2014-01-01 00:00:00"
	elif isinstance(input,long):
		output=str(input)
	elif isinstance(input,int):
		output=str(input)
	elif isinstance(input,unicode):
		output=input.encode('utf8')
	elif isinstance(input,float):
		output=str(int(input))
	return output

#========================================= exe sql
def GetWhere(data):
	wsql = " where "
	if isinstance(data,str) or isinstance(data,unicode):
	    return wsql + data
	for key in data:
	    if str(data[key]).isdigit():
	        wsql = wsql + "%s=%s and "%(key,trans2str(data[key]))
	    else:
	        wsql = wsql + "%s='%s' and "%(key,trans2str(data[key]))
	return wsql[0:-4]
    
#=================================== 插入
def _ExeInsert(cursor,table,data,ignore_key="id",output=False):
	rsql = "insert into " + table + "("
	value = ") value("
	rlist = []
	for key in data:
	    rsql = rsql + key + ','
	    value = value + "%s,"
	    rlist.append(trans2str(data[key]))
	rsql = rsql[0:-1]
	value = value[0:-1]
	rsql = rsql + value + ") on duplicate key update %s=%s"%(ignore_key,ignore_key)
	if output:
		print rsql%tuple(rlist)
	return cursor.execute(rsql,rlist)

def _ExeInsertList(cursor,table,datas,ignore_key="id",output=False):
	rsql = "insert into " + table + "("
	value = ") value("
	rlist = []
	data1 = datas[0]
	for key in data1:
	    rsql = rsql + key + ','
	    value = value + "%s,"
	for data in datas:
		rdata = []
		for k,v in data.items():
			rdata.append(trans2str(v))
		rlist.append(rdata)
	rsql = rsql[0:-1]
	value = value[0:-1]
	#rsql = rsql + value + ") on duplicate key update %s=%s"%(ignore_key,ignore_key)
	rsql = rsql + value + ")"
	if output:
		print rsql
	return cursor.executemany(rsql,rlist)

def ExeInsert(cursor,table,data,ignore_key="id",output=False):
	if isinstance(data,list):
		return _ExeInsertList(cursor,table,data,ignore_key,output)
	else:
		return _ExeInsert(cursor,table,data,ignore_key,output)

#======================================== update
def ExeUpdate(cursor,table,data,where_data,output=False):
	rsql = "update " + table + " set "
	rlist = []
	for key in data:
	    rsql = rsql + key + "=%s,"
	    rlist.append(trans2str(data[key]))
	rsql = rsql[0:-1]
	rsql = rsql + GetWhere(where_data)
	if output:
		print rsql%tuple(rlist)
	return cursor.execute(rsql,rlist)

#======================================== select
#通过sql条件查询数据库，可以有多个条件或直接sql的判断语句
def _ExeSelectSql(cursor,table,keylist,where_data,one=False,output=False):
	rsql = "select "
	for key in keylist:
	    rsql = rsql + key + ","
	rsql = rsql[0:-1]
	rsql = rsql + " from " + table + GetWhere(where_data)
	cursor.execute(rsql)
	if output:
		print rsql
	if one:
	    return cursor.fetchone()
	else:
	    return cursor.fetchall()

#退过一个字段的key队列查询数据库，条件只能是一个所以要用唯一key
def _ExeSelectList(cursor,table,keylist,where_data,one=False,output=False):
	rsql = "select "
	for key in keylist:
	    rsql = rsql + key + ","
	rsql = rsql[0:-1]
	rsql = rsql + " from " + table 
	where = " where "
	for key in where_data[0]:
		where += key + " in ("
		break
	for item in where_data:
		for k,v in item.items():
			where += "'%s',"%v
	rsql  = rsql + where[:-1] + ")"
	cursor.execute(rsql)
	if output:
		print rsql
	if one:
	    return cursor.fetchone()
	else:
	    return cursor.fetchall()

#通过判断where_data的类型来决定调用哪个数
def _ExeSelect(cursor,table,keylist,where_data,one=False,output=False):
	if isinstance(where_data,list):
		return _ExeSelectList(cursor,table,keylist,where_data,one,output)
	else:
		return _ExeSelectSql(cursor,table,keylist,where_data,one,output)

#外部调用，通过table传表信息，可以兼容分表的情况
def ExeSelect(cursor,table,keylist,where_data,one=False,output=False):
    division = 1
    if isinstance(table,dict):
        division = table["division"]
        table = table["name"]
    result = []
    for i in range(0,division):
        if division == 1:
            rows = _ExeSelect(cursor,table,keylist,where_data,one,output)
            result = rows
        else:
            rows = _ExeSelect(cursor,table+str(i),keylist,where_data,one,output)
            for row in rows:
                result.append(row)
    return result

#把数据库返回的结果转换成以 某个字段为key的dict
#ret：以某字段为key的dict里是数据库的行结果
def transMysqlRetDict(rows,key,columns=None):
	result = {}
	if isinstance(rows[0],dict):	
		for row in rows:
			result[row[key]] = row
	elif isinstance(rows[0],list) and columns:
		index = 0
		for i in range(0,len(columns)):
			if key == columns[i]:
				index = i
				break
		for row in rows:
			result[row[index]] = row

#=========================================== 是否在数据库里
def _isInDatabase(cursor,table,data):
    rsql = "select "
    rwhere = " where "
    keylist = []
    for key in data:
        rsql = rsql + key + ","
        rwhere = rwhere + key + "=%s and "
        keylist.append(data[key])
    rsql = rsql[0:-1]
    rwhere = rwhere[0:-4]
    rsql = rsql + " from " + table + rwhere
    cursor.execute(rsql,keylist)
    row = cursor.fetchone()
    if row:
        return True
    else:
        return False
            
#参数data为[{key:value}]
#key只能是一个字段，返回的结果为dict，key是库里有的key字段的数据
def _isInDatabaseList(cursor,table,data):
	key = ""
	for k in data[0]:
		key = trans2str(k)
		break
	rows = _ExeSelectList(cursor,table,[key],data)
	ret = {} 
	for row in rows:
		if isinstance(row,dict):
			ret[row[key]] = 1
		else:
			ret[row[0]] = 1
	return ret

def isInDatabase(cursor,table,data):
	if isinstance(data,list):
		return _isInDatabaseList(cursor,table,data)
	else:
		return _isInDatabase(cursor,table,data)

#============================================ 其他
#将数据加入redis，后面会统一入库
#数据为dict，key是字段名
def data2redis(data,rc,queue,table,type,key):
	result = {}
	result["table"] = table
	result["type"] = type
	result["key"] = key
	result["data"] = data
	jstr = json.dumps(result,ensure_ascii=False)
	return rc.lpush(queue,jstr)
