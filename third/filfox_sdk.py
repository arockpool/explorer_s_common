import uuid
import json
import logging
import time
import datetime
import requests
import traceback
from urllib import parse

from explorer_s_common import debug, utils, consts, decorator


class FilfoxBase(object):

    def __init__(self, net='spacerace'):
        self.net = net
        if net == 'calibration':
            self.host = 'https://calibration.filfox.info'
        else:
            self.host = 'https://filfox.info'

    def fetch(self, url, headers={}, params={}, data={}):
        try:
            logging.warning('url--> %s, params--> %s' % (url, params))
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36',
                "locale": "zh"}
            result = requests.get(url, headers=headers, params=params, data=data, timeout=30).json()
            # logging.warning('response--> %s' % result)
            return result
        except Exception as e:
            debug.get_debug_detail(e)
            return {}

    def get_blocks(self, page_size=100, page_index=0, duration='1y'):
        '''
        获取出块排行(0版本)
        '''
        url = self.host + '/api/v1/miner/list/blocks'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index, 'duration': duration})

    def get_blocks_v1(self, page_size=100, page_index=0, duration='24h'):
        '''
        获取出块排行(1版本)
        '''
        url = self.host + '/api/v1/miner/list/blocks'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index, 'duration': duration})

    def get_overview(self):
        '''
        获取总览
        '''

        if self.net == 'calibration':
            url = 'https://calibration.filfox.info/zh'
        else:
            url = 'https://filfox.info/zh/'

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}
            return requests.get(url, headers=headers, timeout=30)

        except Exception as e:
            debug.get_debug_detail(e)
            return ''

    def get_overview_2(self):
        '''
        api方式获取
        '''
        url = self.host + '/api/v1/overview'
        return self.fetch(url=url, params={})

    def get_gas_stat(self):
        '''
        获取gas统计
        '''

        url = 'https://filfox.info/zh/stats/gas'

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'}
            return requests.get(url, headers=headers, timeout=30)

        except Exception as e:
            debug.get_debug_detail(e)
            return ''

    def get_power_increase(self, page_size=100, page_index=0, duration='7d'):
        '''
        挖矿排行榜-获取算力增量
        '''
        url = self.host + '/api/v1/miner/list/power-growth'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index, 'duration': duration})

    def get_power_valid(self, page_size=50, page_index=0):
        '''
        挖矿排行榜-有效算力
        '''
        url = self.host + '/api/v1/miner/list/power?pageSize={}&page={}'.format(page_size, page_index)
        return self.fetch(url=url)

    def get_power_valid_index(self, count=20):
        '''
        挖矿排行榜-有效算力
        '''
        url = self.host + '/api/v1/miner/list/power?count={}'.format(count)
        return self.fetch(url=url)

    def get_miner_ranking(self, page_size=100):
        """
        挖矿排行--出块数(前20个)
        :param page_size:
        :return:
        """
        url = self.host + '/api/v1/miner/top-miners/power'
        return self.fetch(url=url, params={'count': page_size})

    def get_miner_increase_ranking(self, page_size=100, duration='24h'):
        url = self.host + '/api/v1/miner/top-miners/power-growth'
        return self.fetch(url=url, params={'count': page_size, 'duration': duration})

    def get_block_list(self, page_size=10):
        url = self.host + '/api/v1/tipset/recent'
        return self.fetch(url=url, params={'count': page_size})

    def search(self, value):
        url = self.host + '/api/v1/search'
        return self.fetch(url=url, params={'id': value})

    def get_balance_list(self, page_size=10, page_index=0):
        url = self.host + '/api/v1/rich-list'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index})

    def get_miner_power_stats(self, miner_address):
        url = self.host + '/api/v1/address/' + miner_address + '/power-stats'
        return self.fetch(url=url)

    def get_address_mining_stats(self, address_id, duration):
        url = self.host + '/api/v1/address/' + address_id + '/mining-stats'
        return self.fetch(url=url, params={'duration': duration, })

    def get_miner_address_balance_stats(self, miner_address):
        url = self.host + '/api/v1/address/' + miner_address + '/balance-stats'
        return self.fetch(url=url)

    def get_miner_address_balance_stats_detail(self, miner_address):
        url = self.host + '/api/v1/address/' + miner_address + '/balance-stats'
        return self.fetch(url=url, params={"duration": "24h", "samples": 48})

    def get_miner_overview(self, miner_address):
        url = self.host + '/api/v1/address/' + miner_address
        return self.fetch(url=url)

    def get_address_message(self, miner_address, page_index=0, page_size=20, method=None):
        url = self.host + '/api/v1/address/' + miner_address + '/messages'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index, "method": method})

    def get_miner_block(self, miner_address, page_index=0, page_size=100):
        url = self.host + '/api/v1/address/' + miner_address + '/blocks?pageSize={}&page={}'.format(page_size,
                                                                                                    page_index)
        return self.fetch(url=url)

    def get_miner_transfers(self, miner_address, page_index=0, page_size=100):
        url = self.host + '/api/v1/address/' + miner_address + '/transfers?pageSize={}&page={}'.format(page_size,
                                                                                                       page_index)
        return self.fetch(url=url)

    def get_tipset_list(self, page_size=100, page_index=0):
        url = self.host + '/api/v1/tipset/list'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index})

    def get_message_list(self, page_size=30, page_index=0):
        url = self.host + '/api/v1/message/list'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index})

    def get_block_info(self, page_size=30, page_index=0):
        url = self.host + '/api/v1/message/list'
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index})

    def high_info(self, high):
        url = self.host + '/api/v1/tipset/{}'.format(high)
        return self.fetch(url=url)

    def block_id_info(self, block_id):
        url = self.host + '/api/v1/block/{}'.format(block_id)
        return self.fetch(url=url)

    def by_block_id_get_message_list(self, block_id, page_index, page_size):
        url = self.host + '/api/v1/block/{}/messages'.format(block_id)
        return self.fetch(url=url, params={'pageSize': page_size, 'page': page_index})

    def get_message_info_by_message_id(self, message_id):
        url = self.host + '/api/v1/message/{}'.format(message_id)
        return self.fetch(url=url)

    def get_peer_info(self, peer_id):
        url = self.host + '/api/v1/peer//{}'.format(peer_id)
        return self.fetch(url=url)

    def get_tipset(self, tipset):
        url = self.host + '/api/v1/tipset/' + tipset
        return self.fetch(url=url, params={})

    def get_block_distribution(self):
        url = self.host + '/api/v1/miner/top-miners/power/brief'
        return self.fetch(url=url, params={"count": 20})

    def get_miner_power_increment_tendency(self, count=5, duration="7d", samples=7):
        url = self.host + '/api/v1/stats/miner/power-growth'
        return self.fetch(url=url, params={"count": count, "duration": duration, "samples": samples})

    def get_mining_earnings(self, duration="7d"):
        url = self.host + '/api/v1/stats/miner/reward-per-byte'
        return self.fetch(url=url, params={"duration": duration})

    def get_sector_pledge(self, duration="7d"):
        url = self.host + '/api/v1/stats/miner/sector-initial-pledge'
        return self.fetch(url=url, params={"duration": duration})

    def get_gas_tendency(self, duration="7d", samples="48"):
        url = self.host + '/api/v1/stats/base-fee'
        return self.fetch(url=url, params={"duration": duration, "samples": samples})

    def get_gas_data_24h(self):
        url = self.host + '/api/v1/stats/message/fee'
        return self.fetch(url=url)

    def get_address_message_send(self, miner_address, page_index=0, page_size=20, method="Send"):
        url = self.host + '/api/v1/address/' + miner_address + '/messages?pageSize={}&page={}&method={}'.format(
            page_size, page_index, method
        )
        return self.fetch(url=url)
