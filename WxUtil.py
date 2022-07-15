#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
from RedisPool import RedisPool
import requests
from requests_toolbelt import MultipartEncoder
from Config import getConfig

import sys
if sys.version < '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class Singleton(object):
    def __init__(self, cls):
        self._cls = cls
        self._instance = {}

    def __call__(self,path):
        if self._cls not in self._instance:
            self._instance[self._cls] = self._cls(path)
        return self._instance[self._cls]


@Singleton
class WxUtil(object):
    def __init__(self,path):
        nowTime = int(time.time())
        self.path = path
        self.config = getConfig()
        # 如果缓存中有 access_token 未过期的 从缓存初始化
        accessToken = RedisPool.getConn().get(RedisPool.WXKFACTOKEN)
        accessTokenTTL =  RedisPool.getConn().ttl(RedisPool.WXKFACTOKEN)
        self.__access_token = None
        self.__access_token_expires_in = 0
        if accessTokenTTL > 20 and accessToken != None and len(accessToken) > 1:
            self.__access_token = accessToken
            self.__access_token_expires_in = nowTime + accessTokenTTL - 1

        ## 如果缓存中有 media_id 未过期的 从缓存初始化
        mediaId = RedisPool.getConn().get(RedisPool.WXKFMEDIAID)
        mediaIdTTL = RedisPool.getConn().ttl(RedisPool.WXKFMEDIAID)
        self.__media_id = None
        self.__media_id_expires_in = 0
        if mediaIdTTL > 20 and mediaId != None and len(mediaId) > 1:
            self.__media_id = mediaId
            self.__media_id_expires_in = nowTime + mediaIdTTL -1;


        # next_cursor 最好是从数据库里读
        self.next_cursor = '4gw7MepFLfgF2VC5nov'
        self.msgToken = None

    def upload(self,fileName,path,access_token):
        url = "https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token=%s&type=image" % access_token

        form = {'file_type': 'stream',
                'file_name': '%s' % fileName,
                'file': (fileName, open(path, 'rb'),
                         'multipart/form-data')}  # 需要替换具体的path  具体的格式参考  https://www.w3school.com.cn/media/media_mimeref.asp
        multi_form = MultipartEncoder(form)
        headers = {}
        headers['Content-Type'] = multi_form.content_type
        response = requests.request("POST", url, headers=headers, data=multi_form)
        print response.content
        retJson = response.json()
        media_id = retJson['media_id']
        created_at = int(retJson['created_at'])
        self.__media_id = media_id
        # 资源有效期3天 保险一点 2.5天   就不用了
        _ttl = 60*60*(24*3 - 12 )
        self.__media_id_expires_in = int(time.time()) + _ttl
        RedisPool.getConn().set(RedisPool.WXKFMEDIAID,media_id,_ttl)
        return media_id,created_at

    def getAccessToken(self):
        newTime = int(time.time())
        if self.__access_token == None or self.__access_token_expires_in < newTime:
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s" % (self.config.weixinkf.appid,self.config.weixinkf.corpsecret)
            response = requests.request("GET", url)
            print response,response.content
            retJson = response.json()
            access_token = retJson['access_token']
            self.__access_token = access_token
            self.__access_token_expires_in = int(time.time()) + 7000
            RedisPool.getConn().set(RedisPool.WXKFACTOKEN,access_token,6900)
        return self.__access_token

    def getmediaId(self):
        access_token = self.getAccessToken()
        newTime = int(time.time())
        if self.__media_id == None or self.__media_id_expires_in < newTime:
            self.upload(self.config.weixinkf.kfimg, "%s/%s" % (self.path,self.config.weixinkf.kfimg), access_token)
        return self.__media_id

    def doTest(self):
        print self.config.weixinkf.welcome_text
        print self.getmediaId()
        self.send_text()
    def getNextCursor(self):
        #这里加逻辑去数据库读
        self.next_cursor = RedisPool.getConn().get(RedisPool.WXKFNEXTCURSOR)
        return self.next_cursor
    def setNextCursor(self,next_cursor):
        #更新到数据库
        self.next_cursor = next_cursor
        RedisPool.getConn().set(RedisPool.WXKFNEXTCURSOR,next_cursor)

    def getMsgToken(self):
        # 这个需要从监听那边同步过来 10分钟有效期
        self.msgToken = RedisPool.getConn().get(RedisPool.WXKFTKOKEN)
        return self.msgToken

    def get_message(self):
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg?access_token=%s" % self.getAccessToken()
        token = self.getMsgToken()
        data = {
            "cursor": self.getNextCursor(),
            "token": self.getMsgToken(),
            "limit": 10,
            "voice_format": 0
        }
        if token == None:
            data = {
                "cursor": self.getNextCursor(),
                "limit": 10,
                "voice_format": 0
            }
        headers = {}
        headers['Content-Type'] = "application/json"
        response = requests.request("POST", url,headers=headers,data=json.dumps(data))
        print json.dumps(data),response.content
        return response.json()

    def send_text(self,touser,open_kfid,text):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token=%s' % self.getAccessToken()
        data = {
           "touser" : touser,
           "open_kfid": open_kfid,
           # "msgid": "MSGID",
           "msgtype" : "text",
           "text" : {
               "content" : text
                }
            }
        headers = {}
        headers['Content-Type'] = "application/json"
        response = requests.request("POST", url, headers=headers, data=json.dumps(data))
        print response.content
        return response.json()
    def send_welcome(self,code):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg_on_event?access_token=%s' % self.getAccessToken()
        data = {
                "code": code,
                "msgtype": "msgmenu",
                "msgmenu": {
                    "head_content": "欢迎咨询",
                    "list": [
                        {
                            "type": "click",
                            "click":
                            {
                                "id": "101",
                                "content": "接入人工"
                            }
                          },
                        {
                            "type": "view",
                            "view": {
                                "url": self.config.weixinkf.qrurl,
                                "content": "点击查看客服联系方式"
                            }
                        }
                    ],
                    "tail_content": self.config.weixinkf.tail_content
                }
            }
        headers = {}
        headers['Content-Type'] = "application/json"
        response = requests.request("POST", url, headers=headers, data=json.dumps(data))
        print response.content
        return response.json()

    def send_media(self,touser,open_kfid,media_type,media_id):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token=%s' % self.getAccessToken()
        data = {
           "touser" : touser,
           "open_kfid": open_kfid,
           # "msgid": "MSGID",
           "msgtype" : media_type,
           media_type : {
               "media_id" : media_id
                }
            }
        headers = {}
        headers['Content-Type'] = "application/json"
        response = requests.request("POST", url, headers=headers, data=json.dumps(data))
        print response.content
        return response.json()


    def read_msg(self):
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
    PATH = "."
    DEBUG =True
    wxUtil = WxUtil(PATH)
    #测试消息
    wxUtil.send_text("wmtKfgDAAAuHiUdoZUVe5sW6wdLJqAJA","wktKfgDAAARQjCf_Z2w1nhMzD7pOF0NA","开始干活")
    # wxUtil.send_media("wmtKfgDAAAuHiUdoZUVe5sW6wdLJqAJA", "wktKfgDAAARQjCf_Z2w1nhMzD7pOF0NA","image",wxUtil.getmediaId())

    # wxUtil.read_msg()
    old_token = "go go go ……"
    while True:
        token = wxUtil.getMsgToken()
        if token != None and token != old_token:
            wxUtil.read_msg()
            old_token = token
        else:
            print('sleep 3 wait event')
            time.sleep(3)
