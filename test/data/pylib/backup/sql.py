#!/usr/bin/python
#coding=utf-8
import sys
from sre_compile import isstring
reload(sys)
#sys.setdefaultencoding("utf-8")

#======================================= get sql
def InsertSql(table ,keylist):
    rsql = "insert into " + table +"("
    value = ") value("
    for key in keylist:
        rsql = rsql + key + ','
        value = value + "%s,"
    rsql = rsql[0:-1]
    value = value[0:-1]
    rsql = rsql + value + ")"
    return rsql

def UpdateSql(table,keylist,where):
    rsql = "update " + table + " set "
    for key in keylist:
        rsql = rsql + key + "=%s,"
    rsql = rsql[0:-1]
    rsql = rsql + " " + where
    return rsql

#========================================= exe sql
def GetWhere(data):
	wsql = " where "
	if isstring(data):
	    return wsql + data
	for key in data:
	    if str(data[key]).isdigit():
	        wsql = wsql + "%s=%s and "%(key,data[key])
	    else:
	        wsql = wsql + "%s='%s' and "%(key,data[key])
	return wsql[0:-4]
    
def ExeInsert(cursor,table,data):
    rsql = "insert into " + table + "("
    value = ") value("
    rlist = []
    for key in data:
        rsql = rsql + key + ','
        value = value + "%s,"
        rlist.append(str(data[key]).encode('utf-8'))
    rsql = rsql[0:-1]
    value = value[0:-1]
    rsql = rsql + value + ")"
    return cursor.execute(rsql,rlist)

def ExeUpdate(cursor,table,data,where_data):
	rsql = "update " + table + " set "
	rlist = []
	for key in data:
	    rsql = rsql + key + "=%s,"
	    rlist.append(str(data[key]).encode('utf-8'))
	rsql = rsql[0:-1]
	rsql = rsql + GetWhere(where_data)
	return cursor.execute(rsql,rlist)

def ExeSelect(cursor,table,keylist,where_data,one=False):
	rsql = "select "
	for key in keylist:
	    rsql = rsql + key + ","
	rsql = rsql[0:-1]
	rsql = rsql + " from " + table + GetWhere(where_data)
	cursor.execute(rsql)
	if one:
	    return cursor.fetchone()
	else:
	    return cursor.fetchall()
            
#=========================================== check sql
# def isInDatabase(cursor,checksql):
#     cursor.execute(checksql)
#     row = cursor.fetchone()
#     if row:
#         return True
#     else:
#         return False
    
def isInDatabase(cursor,table,data):
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
            


        
        
        
        
        
        
        
        
    
    
