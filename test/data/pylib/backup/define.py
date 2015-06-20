#!/usr/bin/python
#coding=utf-8
import logging
import urllib
import urllib2
import re
import os
import time
import MySQLdb
import socket
import hashlib
import gzip
import StringIO
import threading
import Queue
import logging.handlers
import redis
import pymssql
import chardet
import BeautifulSoup

finish = 0
#===================================== sql ==============================
def GetCursor(server,db,type=0):
	_host = server["host"]
	_user = server["user"]
	_pw = server["pw"]
	cursor = None
	if type == 0: #mysql 
		conn = MySQLdb.connect(_host,_user,_pw,db,3306)
		cursor = conn.cursor()
		cursor.execute("set names utf8")
	if type == 1: #sql server
		conn = pymssql.connect(host=_host,user=_user,database=db,password=_pw)
		cursor = conn.cursor()
	return cursor

def postSql(argdic,url):
    request = urllib2.Request(url)
    data = urllib.urlencode(argdic)
    response = urllib2.urlopen(request,data)
    ret = response.read()
    return ret 

def postInsert(table,sku,argdic,url):
    argdic["tblname"] = table
    argdic["packageName"] = sku
    return postSql(argdic,url)

def postUpdate(table,sku,argdic,url):
    argdic["tblname"] = table
    argdic["packageName"] = sku
    return postSql(argdic,url)

def wdjpostInsert(table,sku,argdic):
	url = "http://apk.tongbu.com/api/v1/dbwrite"
	argdic["tblname"] = table
	argdic["packageName"] = sku
	return postSql(argdic,url)

def wdjpostUpdate(table,sku,argdic):
	url = "http://apk.tongbu.com/api/v1/dbupdate"
	argdic["tblname"] = table
	argdic["packageName"] = sku
	return postSql(argdic,url)

#===================================== 正则  ================================
def GetAllMatch(patternStr, content):
    pattern = re.compile(patternStr)
    match = pattern.findall(content)
    return match

def GetFirstMatch(patternStr,content):
    pattern = re.compile(patternStr)
    match = pattern.search(content)
    if match:
        return match
    return match

def GetAllMatch2(pattern1, pattern2 , content):
    match = GetAllMatch(pattern1,content)
    parentList = []
    if match:
        for item in match:
            subList = GetAllMatch(pattern2,item)
            parentList.append(subList)
    return parentList

def GetFirstMatchList(pattern1, pattern2 , content):
    match = GetAllMatch(pattern1,content)
    subList = []
    if match:
        item = match[0]
        subList = GetAllMatch(pattern2,item)
    return subList

#================================= util ==================================
def GetRedisClient(server):
	return redis.Redis(host=server["host"],port=server["port"],db=server["db"])

def GetLogger(logfile,flag,name,formatstr=None,level=logging.INFO):
    logger = logging.getLogger(name)
    ch = logging.handlers.RotatingFileHandler(logfile)
    if not formatstr:
        formatstr = "["+flag+"][%(asctime)s][%(filename)s][%(lineno)d][%(levelname)s]::%(message)s"
    formatter = logging.Formatter(formatstr)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(level)
    return logger

def LogConfig(logfile,level=logging.INFO,fmt=None):
    if not fmt:
        fmt = "[%(asctime)s][%(filename)s][%(lineno)d][%(levelname)s]::%(message)s"
    logging.basicConfig(filename=logfile,level=level,format=fmt)

def GetNowDatetime():
    return time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(time.time()))

def ExecuteSqlEx(cursor,sql):
    start_time = time.time()
    cursor.execute(sql)
    cost = time.time() - start_time
    row = cursor.fetchone()
    return (row,cost)

def Getip():
    ip = socket.gethostbyname(socket.gethostname())
    return ip
    
def getApkid(sku):
    md5 = hashlib.md5(sku).hexdigest()
    high = hex2dec(md5[1:16])
    low = hex2dec(md5[17:32])
    apkid = int(high) + int(low)
    return apkid
    
def GetMd5(string):
    return hashlib.md5(string).hexdigest()

def GetFileMd5(strFile):  
    fi = None;  
    bRet = False;  
    strMd5 = "";  
    try:  
        fi = open(strFile, "rb");  
        md5 = hashlib.md5();  
        strRead = "";  
        while True:  
            strRead = fi.read(8096);  
            if not strRead:  
                break;  
            md5.update(strRead);  
        #read file finish  
        bRet = True;  
        strMd5 = md5.hexdigest();  
    except:  
        bRet = False;  
    finally:   
        if fi:  
            fi.close()  
    return strMd5 
    
def GetMp3Info(mp3,flag=""):
	tmpfile = "/tmp/mp3info.tmp" + flag
	os.system("cutmp3 -I " + mp3 + " >" + tmpfile)
	tmp = open(tmpfile)
	info = tmp.read()
	tmp.close()
	return info

def GetMp3Length(mp3):
	info = GetMp3Info(mp3)
	s_index = info.index("second(s)")
	m_index = info.index("minute(s)")
	second = int(float(info[s_index - 8:s_index-1].split(" ")[-1]))
	minute = int(info[m_index-5:m_index-1].split(" ")[-1])
	length = minute * 60 + second
	return length

def GetMd5Path(md5):
	return md5[-1] + '/' + md5[29:-1] + '/'	
	
#================================== 网络  ===================================
def DeGzip(data):
    cmps = StringIO.StringIO(data)
    gzipper = gzip.GzipFile(fileobj=cmps)
    return gzipper.read()

def Post(url,data,heads = {},datatype=True):
    request = urllib2.Request(url)
    data = urllib.urlencode(data)
    for key in heads:
        request.add_header(key, heads[key])
    response = urllib2.urlopen(request,data,timeout=10)
    code = response.getcode()
    if datatype:
        return (code,response.read())
    else:
        return (code,response)

g_proxy_list = [] 
g_proxy_index = [0]
def InitProxy(proxy_file):
	f_proxy = open(proxy_file,"r+")
	lines = f_proxy.readlines()	
	f_proxy.close()
	count = 0
	for line in lines:
		line = line.replace("\t"," ")
		line = line.replace("\n","")
		ip = line.split(" ")[0]
		desc = line.split(" ")[-1]
		proxy = {"http":ip,"count":count,"desc":desc}
		count = count + 1
		g_proxy_list.append(proxy)

def ProxyPost(url,data,heads = {},datatype=True):
	retry = 3 
	proxy = g_proxy_list[g_proxy_index[0]]		
	g_proxy_index[0] = g_proxy_index[0] + 1
	proxy_handler = urllib2.ProxyHandler(proxy)
	opener = urllib2.build_opener(proxy_handler)
	request = urllib2.Request(url)
	data = urllib.urlencode(data)
	for key in heads:
	    request.add_header(key, heads[key])
	while retry:
		try:
			response = opener.open(request,data,timeout=10)
			code = response.getcode()
			if datatype:
			    return (code,response.read())
			else:
			    return (code,response)
		except Exception,e:
			retry = retry - 1
			if retry == 0:
				print proxy,e
				return (-1,"")

def ProxyGet(url,heads = {},datatype=True):
	retry = 3 
	proxy = g_proxy_list[g_proxy_index[0]%len(g_proxy_list)]		
	g_proxy_index[0] = g_proxy_index[0] + 1
	proxy_handler = urllib2.ProxyHandler(proxy)
	opener = urllib2.build_opener(proxy_handler)
	request = urllib2.Request(url)
	for key in heads:
	    request.add_header(key, heads[key])
	while retry:	
		try:
			response = opener.open(request,timeout=10)
			code = response.getcode()
			if datatype:
			    return (code,response.read())
			else:
			    return (code,response)
		except Exception,e:
			retry = retry - 1 
			if retry == 0:
				print proxy,e
				return (-1,"")
    
def DownloadFile(url,local,head=None):
    retry = True
    while retry:
        try:
            request = urllib2.Request(url)
            request.add_header("User-Agent","Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36g")
            uf = urllib2.urlopen(request, timeout=10)
            tmpdata = uf.read(64*1024)
            of = open(local,"wb+")
            while tmpdata:
                of.write(tmpdata)
                tmpdata = uf.read(64*1024)
            of.close()
            uf.close()
            return True
        except Exception,e:
            #print e
            retry = False
    return False
    
def UrlEncode(url):
    url = url.encode('utf-8')
    p = repr(url).replace(r'\x', '%')
    return p[1:-1]

def UrlQuote(url):
    url = urllib.quote(url)
    url = url.replace("/","%2F")
    return url

def crawl_url(url,heads={}):
    fails=0
    html=""
    code=200
    time.sleep(0.2)
    start = time.time()
    while True:
        try:
			if fails>=3:
			    code=-1
			    break
			request=urllib2.Request(url)
			request.add_header("version","HTTP/1.1")
			request.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36")
			request.add_header("Accept-Encoding","identity")
			for key in heads:
			    request.add_header(key,heads[key])
			res_page=urllib2.urlopen(request,timeout=12)
			code=res_page.getcode()
			headerinfo=res_page.info()
			if ("Content-Length" in headerinfo) and int(headerinfo['Content-Length'])>1048576:
			    code=99
			    html=""
			else:
			    html=res_page.read()
			if "Content-Encoding" in headerinfo and 'gzip' in headerinfo["Content-Encoding"]:
				html=DeGzip(html)
        except Exception,e:
            print e
            time.sleep(1)
            fails+=1
        else:
            res_page.close()
            break
    return (code,html)

def crawl_gzip_url(url):
    (code,html) = crawl_url(url, {"Accept-Encoding":"gzip"})
    if code ==200:
        html = DeGzip(html)
    return (code,html)
#============================================================================== 转换
# base = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F]
base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]

# bin2dec
def bin2dec(string_num):
    return str(int(string_num, 2))

# hex2dec
def hex2dec(string_num):
    return str(int(string_num.upper(), 16))

# dec2bin
def dec2bin(string_num):
    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num,rem = divmod(num, 2)
        mid.append(base[rem])
    return ''.join([str(x) for x in mid[::-1]])

# dec2hex
def dec2hex(string_num):
    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num,rem = divmod(num, 16)
        mid.append(base[rem])
    return ''.join([str(x) for x in mid[::-1]])

# hex2tobin
def hex2bin(string_num):
    return dec2bin(hex2dec(string_num.upper()))

# bin2hex
def bin2hex(string_num):
    return dec2hex(bin2dec(string_num))

def getUrlmd5i(strmd5):
    return hex2dec(str(strmd5)[0:13])

#================================================================ thread

class mythread(threading.Thread):
    def __init__(self,num,queue,worker,paramf=None):
        threading.Thread.__init__(self)
        self.num = num
        self.queue = queue
        self.worker = worker
        self.param = None
        if paramf:
            self.param = paramf()
        
    def run(self):
        while True:
            if self.queue.qsize() == 0:
                time.sleep(5)
            item = self.queue.get()
            self.worker(item,self.num,self.param)

g_queue = Queue.Queue()
def init(queue,worker,count,paramf=None):
    g_queue = queue
    for index in range(0,count):
        td = mythread(index,queue,worker,paramf)
        td.start()

def loop(getQueue=None,queue=None,delay=10):
    while True:
        if queue and queue.qsize()==0 and getQueue:
            getQueue()
        time.sleep(delay)
        print "=============== %s %d"%(GetNowDatetime(),g_queue.qsize())
    

##过滤HTML中的标签
#将HTML中标签等信息去掉
#@param htmlstr HTML字符串.
def filter_tags(htmlstr):
	del_list = []
	s = htmlstr

	#blank_line=re.compile('\n+')#去掉多余的空行
	#s=blank_line.sub('\n',s)
	re_br = re.compile('<br\s*?/?>')#处理换行
	s=re_br.sub('\n',s)#将br转换为换行	

	del_list.append(re.compile('<![doctype|DOCTYPE][^>]*>',re.I))#匹配doctype
	del_list.append(re.compile('//<!\[CDATA\[[^>]*//\]\]>',re.I))#匹配CDATA
	del_list.append(re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>',re.I))#Script
	del_list.append(re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>',re.I))#style
	del_list.append(re.compile('</?\w+[^>]*>'))#HTML标签
	del_list.append(re.compile('<!--[^>]*-->'))#HTML注释

	for del_re in del_list:
		s = del_re.sub('',s)

	s=replaceCharEntity(s)#替换实体
	return s
        
        
##替换常用HTML字符实体.
#使用正常的字符替换HTML中特殊的字符实体.
#你可以添加新的实体字符到CHAR_ENTITIES中,处理更多HTML字符实体.
#@param htmlstr HTML字符串.
def replaceCharEntity(htmlstr):
	CHAR_ENTITIES={'nbsp':' ','160':' ',
	'lt':'<','60':'<',
	'gt':'>','62':'>',
	'amp':'&','38':'&',
	'quot':'"','34':'"',}
	
	re_charEntity=re.compile(r'&#?(?P<name>\w+);')
	sz=re_charEntity.search(htmlstr)
	while sz:
		entity=sz.group()#entity全称，如&gt;
		key=sz.group('name')#去除&;后entity,如&gt;为gt
		try:
			htmlstr=re_charEntity.sub(CHAR_ENTITIES[key],htmlstr,1)
			sz=re_charEntity.search(htmlstr)
		except KeyError:
		#以空串代替
			htmlstr=re_charEntity.sub('',htmlstr,1)
			sz=re_charEntity.search(htmlstr)
	return htmlstr

def repalce(s,re_exp,repl_string):
	return re_exp.sub(repl_string,s)

#================================   网页正文提取	
def html_code(html):
	code = chardet.detect(html)["encoding"]
	if not code in ["utf-8","GB2312","gbk"]:
		pos = 0
		try:
			pos = html.index("charset=")
			if pos == -1:
				return False	
		except Exception,e:
			return False
		offset = html[pos:pos+20].index('"')
		code = html[pos+8:pos+offset]
	return code 

def html2utf8(html):
	code = html_code(html)
	if code:
		html = html.decode(code,"ignore").encode('utf-8')
		return html
	return False

def main_text(html,code="utf-8",len_min=0,c_rate_min=0,rc_rate_min=0,c_rate2_min=0,rc_rate2_min=0):
	len_html= float(len(html))
	html	= soup_deal(html,code)	
	content = filter_tags(html) 
	len_con = float(len(content))

	line_lens = lines_len(content) 
	blocks	= block_len(line_lens)
	(s,e)	= get_range(blocks)
	
	rcontent = ""
	cline = content.split('\n')
	for index in range(s,e):
		#print index,line_lens[index],blocks[index],"  ",cline[index]
		if len(cline[index])>1:
			rcontent = rcontent + cline[index] + '\n'

	len_rcon = float(len(rcontent))
	rc_rate = len_rcon/len_con 
	c_rate  = len_con/len_html
	if (rc_rate>rc_rate_min and c_rate>c_rate_min) or (
		rc_rate>rc_rate2_min and c_rate>c_rate2_min) and len_rcon>len_min:
		return rcontent
		#print "--- content len --- ",len_rcon,"/",len_con,"/",len_html,rc_rate,c_rate
	print len(rcontent)
	return False
	
def soup_deal(html,code):
	soup = BeautifulSoup.BeautifulSoup(html,fromEncoding='utf-8')#10830")
	for script in soup.findAll("script"):
		script.extract()
	for style in soup.findAll("style"):
		style.extract()
	return str(soup)

def lines_len(content,plist=None):
	line_list = []
	csp = content.split('\n')
	for index in range(0,len(csp)-1):
		line_list.append(len(csp[index].replace(' ','')))
		index = index + 1
	return line_list

def block_len(line_lens,size=4):
	blocks = [0,0,0,0,0]
	index = size
	for index in range(size,len(line_lens)-size):
		count = 0
		for offset in range(1,size):
			count = count + line_lens[index + offset]
			count = count + line_lens[index - offset]
		count = count + line_lens[index] 
		blocks.append(count)
	return blocks

def get_range(blocks):
	max_block = max(blocks) 
	index = 0
	for index in range(0,len(blocks)):
		if blocks[index] == max_block:
			break
	end	  = index
	start = index 
	while(blocks[start]>40):
		start = start - 1 
	while(end<len(blocks) and blocks[end]>40):
		end = end + 1
	return (start,end)
#=-======================================================
#from collections import defaultdict
#from mmseg.search import seg_txt_search,seg_txt_2_dict
#
#def Mmseg(string):
#	return seg_txt_2_dict(string)	
#


