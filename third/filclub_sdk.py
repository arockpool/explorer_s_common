import uuid
import json
import logging
import time
import datetime
import requests
import traceback
from urllib import parse

from explorer_s_common import debug, utils, consts, decorator


class FilclubBase(object):

    def __init__(self):
        self.host = 'https://api.fil.club'

    def fetch(self, url, headers={}, params={}, data={}, json={}):
        try:
            logging.warning('url--> %s' % url)
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}
            result = requests.get(url, headers=headers, params=params, data=data, json=json, timeout=10).json()
            # logging.warning('response--> %s' % result)
            return result
        except Exception as e:
            debug.get_debug_detail(e)
            return {}

    def get_miner_increase_ranking(self, start_date=None, end_date=None):
        '''
        获取矿工算力增长排名
        '''
        url = self.host + '/v0/ipfsmain/mining/MinerAddPowerOrSeedList'
        return self.fetch(url=url, json={'time_start': start_date, 'time_end': end_date, 'offset': 0, "limit": 25, "sort": "power", "sort_type": -1})

    def get_miner_increase_ranking_chart(self, miners=None, start_date=None, end_date=None):
        '''
        获取矿工算力增长排名图表
        '''
        url = self.host + '/v0/ipfsmain/mining/MinerDayAddPowerOrSeedList'
        return self.fetch(url=url, json={'time_start': start_date, 'time_end': end_date, 'limit': 0, 'miner': miners, 'offset': 0, "limit": 25, "sort": "power", "sort_type": -1})
