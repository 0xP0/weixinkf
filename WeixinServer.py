#!/usr/bin/env python
# -*- coding: utf-8 -*-

from WXBizMsgCrypt import WXBizMsgCrypt,SHA1,Prpcrypt,XMLParse
from RedisPool import RedisPool
from WxUtil import WxUtil
import base64

import tornado.ioloop
import tornado.web
import tornado.autoreload


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        data = {}
        for key in self.request.arguments:
            data[key] = self.get_argument(key)
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(Token, data.get('timestamp', ''), data.get('nonce', ''), data.get('echostr', ''))
        if ret == 0 and data.get('msg_signature','') == signature:
            print "PASS:" ,data['echostr']
            pc = Prpcrypt(base64.b64decode(EncodingAESKey + "="))
            ret, xml_content = pc.decrypt(data['echostr'], AppId)
            self.write(xml_content)
        else:
            print "NO AUTH"
            self.write("NO AUTH")

    def post(self, *args, **kwargs):
        data = {}
        for key in self.request.arguments:
            data[key] = self.get_argument(key)
        wxXBizMsgCrypt = WXBizMsgCrypt(Token,EncodingAESKey,AppId)
        ret,xml_content = wxXBizMsgCrypt.DecryptMsg(self.request.body,data.get('msg_signature',''),data.get('timestamp',''),data.get('nonce',''))
        print data
        print xml_content
        if ret == 0:
            xmlParse = XMLParse()
            ret, token = xmlParse.extractByKey(xml_content, "Token")
            print ret, token
            if ret == 0 and token!=None and len(token)> 1:
                RedisPool.getConn().set(RedisPool.WXKFTKOKEN,token,600)
        # self.write("")

def make_app():
    print ("Start App port:8888")
    return tornado.web.Application([
        (r"/wxkf/callback", MainHandler),
    ],debug=True)

if __name__ == "__main__":
    PATH = "."
    wxUtil = WxUtil(PATH)

    EncodingAESKey = wxUtil.config.weixinkf.aeskey
    Token = wxUtil.config.weixinkf.token
    AppId = wxUtil.config.weixinkf.appid

    print "AppId:" + AppId

    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
