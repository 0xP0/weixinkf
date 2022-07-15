import redis
import json
from Config import getConfig
import os
class RedisPool:
    instance = None
    WXKFTKOKEN = "weixinkfToken"
    WXKFNEXTCURSOR = "weixinkfNextCursor"
    def __init__(self):
        config = getConfig()
        self.pool = redis.ConnectionPool(host=config.redis.host, password=config.redis.passwd,
                                         port=config.redis.port, decode_responses=True, db=config.redis.db)
    def __getConnection(self):
        conn = redis.Redis(connection_pool=self.pool)
        return conn

    @classmethod
    def getConn(cls):
        if RedisPool.instance is None:
            RedisPool.instance = RedisPool()
        return RedisPool.instance.__getConnection()

def toStr(obj):
    return json.dumps(obj,default = lambda x: x.__dict__,ensure_ascii=False)

if __name__ == '__main__':
    redisConn = RedisPool.getConn()
    redisConn.set('aaa', 'vvv', 10)
