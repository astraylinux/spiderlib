#!/usr/local/bin/python
#coding=utf-8
import sys
import threading
import time
import Queue
reload(sys)
sys.setdefaultencoding("utf-8")

class Thread(threading.Thread):
	def __init__(self,num,func,queue):
		threading.Thread.__init__(self)
		self.num  = num
		self.func = func
		self.queue = queue

	def run(self):
		while True:
			item = self.queue.get()
			if item is False:
				time.sleep(1)
				return 
			else:
				self.func(item,self.num,self.queue.qsize())
			if self.queue.qsize() == 0:
				time.sleep(1)
				return 

def run(datas,func,num,space=1):
	queue = Queue.Queue()
	for data in datas: 
		queue.put(data)
	for index in range(0,num):
		thread = Thread(index,func,queue)
		thread.start()
		time.sleep(space)
