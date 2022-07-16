#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
from RedisPool import RedisPool
from WxUtil import WxUtil

import sys
if sys.version < '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')



def msgAgent(self):
    has_more = 1
    while has_more == 1:
        datas  = self.get_message()
        has_more = datas.get('has_more',0)
        next_cursor = datas.get('next_cursor',None)
        if next_cursor != None:
            self.setNextCursor(next_cursor)
        msg_list= datas.get('msg_list',[])
        for msg in msg_list:
            origin = msg.get('origin',None)
            msgtype = msg.get('msgtype',None)
            event = msg.get('event',dict())
            send_time = msg.get('send_time', 0)
            external_userid = msg.get('external_userid', None)
            event_type = msg.get('event_type', None)
            open_kfid = msg.get('open_kfid',None)

            now = int(time.time())
            if msgtype != 'event':
                # 非事件消息 都存下来 脚本处理 日报给客服
                RedisPool.getConn().lpush(RedisPool.MESSAGE,json.dumps(msg))

            welcome_code = event.get('welcome_code',None)
            # 发送客服欢迎语
            if welcome_code != None and now - send_time < 20:
                self.send_welcome(welcome_code)
            # 自动回复
            elif origin == 3 and external_userid != None and open_kfid != None and RedisPool.getConn().ttl(RedisPool.WXKFKEEPONEHOUR+external_userid) < 1:
                media_id = self.getmediaId()
                if media_id != None:
                    self.send_text(external_userid,open_kfid,self.config.weixinkf.welcome_text)
                    self.send_media(external_userid,open_kfid,'image',media_id)
                    # 1个小时内 不重复发送
                    RedisPool.getConn().set(RedisPool.WXKFKEEPONEHOUR+external_userid,1,3600)
        if has_more == 0:
            RedisPool.getConn().set(RedisPool.HASNEWMESSAGE,0)

if __name__ == '__main__':
    if __name__ == '__main__':
        PATH = "."
        DEBUG = True
        wxUtil = WxUtil(PATH)
        # 测试消息
        wxUtil.send_text("wmtKfgDAAAuHiUdoZUVe5sW6wdLJqAJA", "wktKfgDAAARQjCf_Z2w1nhMzD7pOF0NA", "开始干活")
        # wxUtil.send_media("wmtKfgDAAAuHiUdoZUVe5sW6wdLJqAJA", "wktKfgDAAARQjCf_Z2w1nhMzD7pOF0NA","image",wxUtil.getmediaId())

        # wxUtil.read_msg()
        old_token = "go go go ……"
        while True:
            token = wxUtil.getMsgToken()
            if token != None and token != old_token:
                msgAgent(wxUtil)
                old_token = token
            else:
                print('sleep 3 wait event')
                time.sleep(3)