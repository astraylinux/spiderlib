#!/usr/bin/python
#coding=utf-8
import re
#import BeautifulSoup
#import chardet
        
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

def html_code(html):
	badcode = {"gbk2312":"gb2312"}
	pos = 0
	try:
		pos = html.lower().find("charset=")
		if pos == -1:
			return False
	except Exception,e:
		return False
		
	cutstr = html[pos:pos+20].lower().replace("charset=","")
	offset = cutstr.rfind('"')
	code = cutstr[:offset].replace("\"","")
	if code.lower() in badcode:
		code = badcode[code.lower()]
	return code 

def html2utf8(html,def_code=None):
	code = html_code(html)
	if code:
		html = html.decode(code,"ignore").encode('utf-8')
		return html
	elif def_code:
		html = html.decode(def_code,"ignore").encode('utf-8')
		return html
	return False
