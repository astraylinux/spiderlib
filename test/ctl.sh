#!/bin/bash

_get_pid(){
	pid=`ps ax |grep "python"|grep "$1"|grep -v grep|awk '{print $1}'`
	echo $pid
}

_start(){
	run $1
	path=`pwd`
	pid=$(_get_pid $path/$1)
	echo "run as $pid"
}

_stop(){
	path=`pwd`
	pid=$(_get_pid $path/$1)
	echo "stop pid: $pid"
	if [[ $pid ]];then
		kill -9 $pid
	fi
}

_restart(){
	_stop $1
	_start $1
}

_suspend(){
	pid=$(_get_pid $1)
	if [[ $pid ]];then
		kill -19 $pid
		echo "suspend pid $pid"
	fi
}

_resume(){
	pid=$(_get_pid $1)
	if [[ $pid ]];then
		kill -18 $pid
		echo "resume pid $pid"
	fi
}

case "$2" in
	"start")
		_start $1
	;;
	"stop")
		_stop $1
	;;
	"restart")
		_restart $1
	;;
	"suspend")
		_suspend $1
	;;
	"resume")
		_resume $1
	;;
	*)
	 echo ""
	 echo "usage: ctl_r2m.sh indexid opt"
	 echo "opt(操作):"
	 echo "  start):开始数据导入程序"
	 echo "  stop):停止程序，使用kill -10，程序会等数据导完再停止"
	 echo "  restart):上面两个命令结合"
	 echo "  suspend):暂停程序，使用kill -19"
	 echo "  resume):唤醒暂停程序，使用kill -18"
	 echo ""
	;;
esac

