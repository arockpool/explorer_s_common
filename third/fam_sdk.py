import json
import random
import time
import datetime
import hashlib
import requests
from urllib import parse

from explorer_s_common import debug, utils, consts, decorator


class FamBase(object):

    def __init__(self):
        self.host = consts.FAM_HOST
        self.app_id = consts.FAM_APP_ID
        self.app_version = '1.0.0'
        self.app_secret = consts.FAM_APP_SECRET

    def getSignature(self):
        '''计算签名'''
        nonce = str(random.randint(1000000000, 9999999999))
        timestamp = str(
            int(datetime.datetime.timestamp(datetime.datetime.now())))

        # 排序
        params = sorted([nonce, timestamp, self.app_secret])
        sorted_params_str = ''.join(params)

        # 计算签名
        sha1 = hashlib.sha1()
        sha1.update(sorted_params_str.encode())
        sign = sha1.hexdigest()

        return 'signature=%s&timestamp=%s&nonce=%s' % (sign, timestamp, nonce)

    def getHeaders(self):
        '''设置headers'''
        return {
            'AppId': self.app_id,
            'AppVersion': self.app_version,
            'Signature': self.getSignature(),
            'Content-type': 'application/x-www-form-urlencoded'
        }

    def fetch(self, url, data, timeout=60):
        try:
            print('request url -->', url)
            print('post data -->', data)
            result = requests.post(url, headers=self.getHeaders(), data=data, timeout=timeout).json()
            # print('response data -->', result)
            return result
        except Exception as e:
            print(e)
            return {}

    def get_pool_miners(self, data={}):
        '''
        获取MINING POOL矿工
        '''
        url = self.host + '/miner/api/miner/get_miner_nos'
        return self.fetch(url=url, data=data)

    def get_project_list(self):
        '''
        获取MINING POOL矿工
        '''
        url = self.host + '/miner/api/miner/get_project_list'
        data = {}
        return self.fetch(url=url, data=data)

    def deposite_notice(self):
        '''
        worker/post钱包余额剩余使用时长查询
        '''
        url = self.host + '/miner/api/wallet/cal_deposite'
        data = {}
        return self.fetch(url=url, data=data)
