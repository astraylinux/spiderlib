#!/usr/bin/python
#coding=utf-8
import re

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
