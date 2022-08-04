import uuid
import json
import logging
import time
import datetime
import requests
import traceback
from urllib import parse

from explorer_s_common import debug, utils, consts, decorator


class FilecoinBase(object):

    def __init__(self):
        self.host = 'https://api.spacerace.filecoin.io'

    def fetch(self, url, headers={}, params={}, data={}, json={}):
        try:
            logging.warning('url--> %s' % url)
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}
            result = requests.get(url, headers=headers, params=params, data=data, json=json, timeout=30).json()
            # logging.warning('response--> %s' % result)
            return result
        except Exception as e:
            debug.get_debug_detail(e)
            return {}

    def get_reward_stat(self, region=None):
        '''
        获取测试网奖励统计
        '''
        url = self.host + '/api/miner/metrics'
        return self.fetch(url=url, params={'region': region})

    def get_sp2_reward_stat(self):
        '''
        获取sp2奖励
        '''
        url = 'https://space-race-2-slingshot-stats.s3.amazonaws.com/prod/clientstats.json'
        return self.fetch(url=url)
