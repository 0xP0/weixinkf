#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import datetime
# 这个只是处理脚本需要 ,并未加入 requirements.txt。 请手动安装
import pytz
print(os.getcwd())

from RedisPool import RedisPool

redisConn = RedisPool.getConn()
messages = redisConn.lrange(RedisPool.MESSAGE,0,-1)
for _message in messages:
    message = json.loads(_message)
    msgtype = message.get('msgtype','event')
    if msgtype != 'event':
        send_time = message.get('send_time',0)
        open_kfid = message.get('open_kfid', "")
        origin = message.get('origin', "")
        external_userid = message.get('external_userid', "")
        content = None
        url = ""
        if msgtype == 'text':
            content = message.get(msgtype, dict()).get("content")
        else:
            content = message.get(msgtype, dict()).get("media_id")
            url = "https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token=%s&media_id=%s" %(redisConn.get(RedisPool.WXKFACTOKEN),content)
        t = datetime.datetime.fromtimestamp(int(send_time), pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        if content != '接入人工':
            print t,content,open_kfid,external_userid,send_time,origin,msgtype,url