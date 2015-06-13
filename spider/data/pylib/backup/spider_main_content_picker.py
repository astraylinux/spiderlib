#!/usr/bin/python
#coding=utf-8
import re
import BeautifulSoup
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
#================================   网页正文提取	
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
