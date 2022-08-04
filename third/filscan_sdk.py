import uuid
import json
import logging
import time
import datetime
import requests
import traceback
from urllib import parse

from explorer_s_common import debug, utils, consts, decorator


class FilscanBase(object):

    def __init__(self):
        self.host = 'https://api.filscan.io:8700'

    def fetch(self, url, headers={}, params={}, data={}, json={}):
        try:
            logging.warning('url--> %s, json --> %s' % (url, json))
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}
            result = requests.post(url, headers=headers, params=params, data=data, json=json, timeout=30).json()
            # logging.warning('response--> %s' % result)
            return result
        except Exception as e:
            debug.get_debug_detail(e)
            return {}

    def get_miner_increase(self, page_index=1, page_size=100):
        '''
        获取矿工算力增量
        '''
        url = self.host + '/rpc/v1'
        return self.fetch(url=url, json={
            "id": 1, "jsonrpc": "2.0", "method": "filscan.MinersEfficiency",
            "params": ["24h", [], page_index * page_size, page_size, 1]
        })

    def get_block_statistics(self):
        '''
        获取矿工算力增量
        '''
        url = self.host + '/rpc/v1'
        return self.fetch(url=url, json={"id": 1, "jsonrpc": "2.0", "params": [], "method": "filscan.BlockCountTrend"})

    def get_block_list(self):
        '''
        获取矿工算力增量
        '''
        url = self.host + '/rpc/v1'
        return self.fetch(url=url, json={"id": 1, "jsonrpc": "2.0", "params": [], "method": "filscan.GetBlockWonList"})

    def get_power_distribution(self):
        '''
        获取算力分布
        '''
        url = self.host + '/rpc/v1'
        return self.fetch(url=url, json={"id": 1, "jsonrpc": "2.0", "params": [], "method": "filscan.ContinentPower"})

    def get_overview(self):
        '''
        获取统计信息
        '''
        url = self.host + '/rpc/v1'
        return self.fetch(url=url, json={"id": 1, "jsonrpc": "2.0", "params": [], "method": "filscan.StatChainInfo"})

    def get_hashrate_ranking(self):
        '''
        获取算力走势
        '''
        url = self.host + '/rpc/v1'
        return self.fetch(url=url, json={"id": 1, "jsonrpc": "2.0", "params": [], "method": "filscan.PowerTrend"})

    def get_miner_power_ranking(self, miner_no):
        '''
        获取miner算力走势(月)
        '''
        url = self.host + '/rpc/v1'
        return self.fetch(url=url, json={"id": 1, "jsonrpc": "2.0", "params": [miner_no, '1m'],
                                         "method": "filscan.MinerTrendInfo"})
