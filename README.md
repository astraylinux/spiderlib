# spiderlib
simple spider lib

![](http://res.astraylinux.com/spider/spiderlib_process.png)
框架是以mysql为存储系统建立的， 主要模块有**dispatcher(任务调度模块)**、**crawler(抓取模块)**、**picker(提取模块)**、**updater(更新模块，暂无)**。另外还有辅助的网络模块**net**，数据库模块**sqld**, 辅助工作模块**tools**。 抓取跟提取的配置是按域名分配，每个域名有一个配置文件，配置着页面的信息，url识别正则，提取xpath配置等，主配置文件是**/test/config.py**，是一些模块的基本配置。而域名配置在**/test/etc/webset**里，这个webset被当成一个python包，增加的页面配置要添加到**__init__.py**中。

spiderlib里的模块都只是代码库，并不能直接执行，可执行程序在test里，可以直接复制出来修改。

下面详细地记录下模块功能。

<!--more-->
## Dispatcher(任务调度)
任务调度模块的工作是从数据库中把需要爬取的网页信息取出来，放到任务队列中，以供后续的程序领取执行。刚开始写爬虫的时候，一般是执行任务的模块直接到库里取数据。这种做法不利于管理，并且很难实现分布式。而使用队列，则由一个程序统一下发任务，调度有问题，也只需要从一个模块找问题。队列还可以很方便地实现分布式，抓取机器到同一台机器领取任务，执行行完后再写回数据，非常方便。后面的sqld模块，也是使用redis队列统一写数据库。
相关配置
```bash
#spider interval config
G_DEFAULT_INTERVAL = 3600*6
G_MIN_INTERVAL	= 3600
G_MAX_INTERVAL = 3600*24*7
G_RISE_INTERVAL = 3600*9

#max dispatch number(new url or update url)
G_MAX_SELECTNUM_NEW = 2000
G_MAX_SELECTNUM_UP = 2000
G_MAX_SELECTNUM_PICK = 2000

#dispatch gap(seconds)
G_DISPATCH_GAP = 10

```

## Crawler(抓取模块)
抓取模块的任务就是从网络上Get页面，并将发现的新链接写回数据库。这套框架里并没有限制抓取模块不能解析页面，而是做了简单的解析，提取链接。而页面要不要保留则是通过配置决定。这里抓取的页面分为**过程页面**和**内容页面**， 过程页面只是用来发现新链接，并不用于后续的信息提取，而内容页面则会用于提取。页面的分辨是通对URL的正则匹配实现的。
主要配置
```bash
#config about database
#division could be 1, 16, 256, the 16 use md5 last char
#256 use the md5 last two char
G_MAINDB = "test"
G_TABLE_LINK = {"name":G_PROJECT_FLAG + "_link", "division":1}

#max run threads of spider and picker
G_MAX_SPIDER_THREAD = 3

############### spider control ################
#if I need save html to database
#if you didn't save the html,you have to download
#the html again where you pick content
G_IFSAVE_HTML = True
#if G_IFSAVE_HTML=True and this is ture
#will save the process html(not detail page)
G_IFSAVE_PASS = False
#if this not True, crawler will not look for new link's from detail page
G_INTO_DETAIL = False
```

## Picker(提取模块)
提取模块用到我之前整理的python常用代码包[**pylib**](https://github.com/astraylinux/pylib)里的提取模块**expath.py**。这是对lxml.etree里的xpath提取部分的简单封装，以实现不更改代码，直接用配置实现不同的提取。Picker模块会试着从html库里取页面数据，如果没有的话，则直接从网上Get页面。根据配置将内容提取出来，并按key value的形式存入数据库。Key是数据库的字段名，因此数据库info库要根据提取内容增加字段。
主要配置
```bash
#max run threads of spider and picker
G_MAX_SPIDER_THREAD = 4

############### site config ####################
G_SITE = etc.webset.SITES
G_SITE_COMMON = etc.common

```

## Updater(更新模块)
待更新。

## Net(网络模块)
Crawler和Picker用到的网络相关的代码都是调用这个模块的。这个模块调用pylib的网络模块增强了get函数。增加了基本的压力控制，从配置来，每个域名，每次Get暂停多少秒。最重要的是实现了DNS缓存，并且保存多个IP地址，执行轮循访问。很多比较大的网站一个域名会有多个IP以实现负载分散，这样通过访问不同的IP避免反抓取，增加抓取线程，提高抓取速度。

## Sqld(Mysql写入模块)
实现这个模块，一来是为了降低Mysql的访问次频率，通过队列，将一些插入指令批量执行。二来是更好地实现分布式，抓取机器将写入数据直接放到队列，可以快速返回。

## Tools(辅助功能模块)
包含了快速建数据库表的函数，新增抓取链接到数据库的函数，quick start.
