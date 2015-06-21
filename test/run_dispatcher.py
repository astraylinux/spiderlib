#!/usr/bin/python
#coding=utf8
import config
from spiderlib import dispatcher

if __name__ == "__main__":
	dispatcher.CONFIG = config
	dper = dispatcher.Dispatcher()
	dper.run()
