#!/usr/bin/python
#coding=utf-8
import sys
import time
import config
from spiderlib import picker
from pylib import util
reload(sys)
sys.setdefaultencoding("utf-8")

#==============================================================
if __name__ == "__main__":
	if len(sys.argv) > 1:
		if sys.argv[1] == "test":
			thread = picker.Picker(0, "test")
		else:
			thread = picker.Picker(0)
		data = {"url":"http://manhua.dmzj.com/yaojingdeweiba/"}
		data["md5"] = util.md5(data["url"])
		data["type"] = 1
		print thread._run(data)
	else:
		for index in range(0, config.G_MAX_PICKER_THREAD):
			thread = picker.Picker(index)
			thread.start()
			time.sleep(1)
		time.sleep(1)
