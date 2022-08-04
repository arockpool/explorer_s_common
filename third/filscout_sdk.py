import uuid
import json
import logging
import time
import datetime
import requests
import traceback
from urllib import parse

from explorer_s_common import debug, utils, consts, decorator


class FilscoutBase(object):

    def __init__(self, net='spacerace'):
        if net != 'spacerace':
            self.host = 'https://filscoutv2api.ipfsunion.cn'
        else:
            self.host = 'https://filscoutv3api.ipfsunion.cn'

    def fetch(self, url, headers={}, params={}, data={}):
        try:
            logging.warning('url--> %s, params --> %s' % (url, params))
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}
            result = requests.get(url, headers=headers, params=params, data=data, timeout=120).json()
            # logging.warning('response--> %s' % result)
            return result
        except Exception as e:
            debug.get_debug_detail(e)
            return {}

    def get_overview(self):
        '''
        获取统计信息
        '''
        url = self.host + '/network/overview'
        return self.fetch(url=url)

    def get_block_list(self):
        '''
        获取最新的出块信息
        '''
        url = self.host + '/tipset/blockChartList'
        return self.fetch(url=url)

    def get_ranking(self, page_size=20, page_index=1):
        '''
        获取排行
        '''
        url = self.host + '/miner/rank'
        return self.fetch(url=url, params={'page_size': page_size, 'page': page_index})

    def get_ranking_by_time(self, ranking_type='quality'):
        '''
        获取排行
        算力走势(有效算力)
        '''
        url = self.host + '/miner/rank_by_time'
        return self.fetch(url=url, params={'type': ranking_type})

    def get_miner_by_address(self, miner_address):
        '''
        获取矿工信息
        '''
        url = self.host + '/account/by_address/' + miner_address
        return self.fetch(url=url)

    def get_miner_block_list(self, miner_id, page_size=20, page_index=1):
        '''
        获取指定矿工的区块列表
        '''
        url = self.host + '/block/list'
        return self.fetch(url=url, params={'miner': miner_id, 'page_size': page_size, 'page': page_index})

    def get_tipset(self, end_height=None, count=10):
        '''
        获取tipset
        '''
        url = self.host + '/tipset/linkedList'
        return self.fetch(url=url, params={'end_height': end_height, 'count': count})

    def get_peer_map(self):
        '''
        获取节点地图
        '''
        url = self.host + '/peer/map'
        return self.fetch(url=url)

    def get_miner_increase_ranking(self, page_index=1, page_size=20):
        '''
        获取算力增速排名
        '''
        url = self.host + '/miner/list_order_by_growth/miner_with_growth_in_one_week'
        return self.fetch(url=url, params={'page': page_index, 'page_size': page_size, 'sector_type': '', 'continent': ''})

    def get_miner_block_ranking(self, page_index=1, page_size=20, search_type='week'):
        '''
        获取矿工的出块排名
        '''
        if search_type == 'week':
            url = self.host + '/miner/list_order_by_blocks/miner_with_blocks_in_one_week'
        else:
            url = self.host + '/miner/list_order_by_blocks/miner_with_blocks_in_24h'
        return self.fetch(url=url, params={'page': page_index, 'page_size': page_size, 'sector_type': '', 'continent': ''})

    def get_miner_balance_ranking(self, page_index=1, page_size=20, actor_type='Storage Miner'):
        '''
        获取矿工的余额排名
        '''
        url = self.host + '/account/list'
        return self.fetch(url=url, params={'page': page_index, 'page_size': page_size, 'actor_type': actor_type})

    def get_miner_list(self, page_index=1, page_size=100):
        '''
        获取矿工列表
        '''
        url = self.host + '/miner/list'
        return self.fetch(url=url, params={'page': page_index, 'page_size': page_size})
