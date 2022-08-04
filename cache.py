import redis
import os
from pickle import dumps, loads

CACHE_SERVER = [os.getenv('REDIS_HOST', "127.0.0.1"), os.getenv('REDIS_PORT', "6379"),
                os.getenv('REDIS_PASSWORD', "redispassword")]

CACHE_TMP = CACHE_SERVER + [1, 'tmp']
CACHE_STATIC = CACHE_SERVER + [2, 'static']
CACHE_API = CACHE_SERVER + [3, 'api']
CACHE_ACCOUNT = CACHE_SERVER + [4, 'account']
CACHE_TEMP = CACHE_SERVER + [0, 'temp']
CONNECTIONS = {}
# 常量保存在redis中的key值
REDIS_KEY = {
    1: "mine_status",  # 矿机状态
    2: "mine_now_status",  # 当前异常的矿机列表
    3: "mine_add_flag",  # 今日矿机同步是否执行标志,value为日期
    4: "mine_error_flag",  # 昨日矿机异常是否执行标志,value为日期
    5: "output_all_data",  # 产出管理-数据汇总
    6: "output_day_data",  # 产出管理-日
}


def get_connection(config):
    global CONNECTIONS
    if config[4] not in CONNECTIONS:
        pool = redis.ConnectionPool(host=config[0], port=config[1], password=config[2], db=config[3])
        connection = CONNECTIONS[config[4]] = redis.Redis(connection_pool=pool)
    else:
        connection = CONNECTIONS[config[4]]
    return connection


def connect_redis(config=CACHE_SERVER, db=0):
    """
    链接redis,默认写入写入0号库
    :param config:
    :return:
    """
    pool = redis.ConnectionPool(host=config[0], port=config[1], password=config[2], db=db)
    connection = redis.Redis(connection_pool=pool)
    return connection


def from_redis_get_str(key, db=0):
    """
    从redis中获取str类型数据
    :param key: redis中的key值
    :return:
    """
    connect = connect_redis(CACHE_SERVER, db=db)
    data = connect.get(key)
    return data


class Cache(object):

    def __init__(self, config=CACHE_TMP):
        '''
        @note: 采用长连接的方式
        '''
        self.conn = get_connection(config)
        # print(help(self.conn.set))

    def get(self, key, original=False):
        '''
        @note: original表示是否是保存原始值，用于incr这样的情况
        '''
        obj = self.conn.get(key)
        if obj:
            return loads(obj) if not original else obj
        return None

    def set(self, key, value, time_out=0, original=False):
        s_value = dumps(value) if not original else value
        time_out = int(time_out)
        if time_out:
            if self.conn.exists(key):
                self.conn.setex(name=key, value=s_value, time=time_out)
            else:
                self.conn.setnx(name=key, value=s_value)
                self.conn.expire(name=key, time=time_out)
        else:
            self.conn.set(name=key, value=s_value)

    def delete(self, key):
        return self.conn.delete(key)

    def incr(self, key, delta=1):
        return self.conn.incrby(key, delta)

    def decr(self, key, delta=1):
        return self.conn.decr(key, delta)

    def exists(self, key):
        return self.conn.exists(key)

    def llen(self, key):
        return self.conn.llen(key)

    def ttl(self, key):
        return self.conn.ttl(key)

    def get_time_is_locked(self, key, time_out):
        '''
        @note: 设置锁定时间
        '''
        key = "tlock_%s" % key
        if self.conn.exists(key):
            return True

        # self.conn.setex(key, '0', time_out)
        self.set(key, 0, time_out)
        return False

    def set_lock(self, key, value, ex=None, px=None, nx=False, xx=False):
        return self.conn.set(key, dumps(value), ex, px, nx, xx)

    def flush(self):
        self.conn.flushdb()


class CacheQueue(Cache):
    '''
    @note: 基于redis的list结构设计一个固定长度的队列
    '''

    def __init__(self, key, max_len, config, time_out=0):
        self.key = "queue_%s" % key
        self.max_len = max_len
        self.time_out = time_out
        self.conn = get_connection(config)

    def push(self, item):
        if self.conn.llen(self.key) < self.max_len:
            self.conn.lpush(self.key, item)
        else:
            def _push(pipe):
                pipe.multi()
                pipe.rpop(self.key)
                pipe.lpush(self.key, item)

            self.conn.transaction(_push, self.key)
        if self.time_out:
            self.conn.expire(self.key, self.time_out)
        # print self.conn.lrange(self.key, 0, -1)

    def pop(self, value, num=0):
        self.conn.lrem(self.key, value, num)

    def init(self, items):
        '''
        @note: 初始化一个列表
        '''
        self.delete()
        if items:
            self.conn.rpush(self.key, *items)

    def delete(self):
        self.conn.delete(self.key)

    def exists(self):
        return self.conn.exists(self.key)

    def __getslice__(self, start, end):
        if not self.conn.exists(self.key):
            return None
        return self.conn.lrange(self.key, start, end)


def get_or_update_data_from_cache(_key, _expire, _cache_config, _must_update_cache, _func, *args, **kwargs):
    """
    @note: 自动缓存方法调用对应的结果，形参名前加下_防止出现重名的和args冲突
    设置data的时候不要设置None值，通过None值来判断是否设置过缓存
    :param _key:
    :param _expire:
    :param _cache_config:
    :param _must_update_cache:
    :param _func:
    :param args:
    :param kwargs:
    :return:
    """
    cache_obj = Cache(config=_cache_config)
    data = cache_obj.get(_key)
    if data is None or _must_update_cache:
        data = _func(*args, **kwargs)
        if data is not None:
            cache_obj.set(_key, data, time_out=_expire)
    return data


if __name__ == '__main__':
    cache_obj = Cache()
    # print cache_obj.set(u'keyaaom@a.c!@#$%^&*()omkeyaaom@a.c!@#$%^&*()om', 'aaa', time_out=1000)
    # print cache_obj.ttl(u'keyaaom@a.c!@#$%^&*()om')

    # cache_queue = CacheQueue('test', 5)
    # cache_queue.push('7')
    # print cache_queue[0:-1]
    # print cache_queue.init(items=[1, 2, 3, 4, 5])
