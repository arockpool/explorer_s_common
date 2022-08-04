import uuid
import json
import logging
import time
import datetime
import requests
import traceback
import base64

from explorer_s_common import debug, utils, consts, decorator


class BbheMngBase(object):

    def __init__(self):
        self.host = consts.BBHEMNG_HOST

    def get_headers(self):
        base64_secret = base64.b64encode(consts.BBHESECRET.encode("utf-8")).decode("utf-8")
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36',
            "Authorization": 'Basic ' + base64_secret
        }

    def get(self, url, params={}, data={}):
        try:
            logging.warning('url--> %s, params--> %s' % (url, params))
            result = requests.get(self.host + url, headers=self.get_headers(), params=params, data=data,
                                  timeout=100).json()
            return result
        except Exception as e:
            debug.get_debug_detail(e)
            return {}

    def post(self, url, data={}):
        try:
            logging.warning('url--> %s, params--> %s' % (url, data))
            result = requests.post(self.host + url, headers=self.get_headers(), data=data, timeout=100).json()
            return result
        except Exception as e:
            debug.get_debug_detail(e)
            return {}

    def get_ribao_overview(self, date):
        '''
        日报节点信息 链上结点算力  date :年月日
        '''
        url = '/ribao/v2/overview'
        return self.get(url, params={'date': date})

    def get_ribao_summary(self, date):
        '''
        机构算力统计
        '''
        url = '/ribao/v2/summary'
        return self.get(url, params={'date': date})

    def get_ribao_cost(self, date, filter_type=-1):
        '''
        每个矿工的日消耗
        '''
        url = '/ribao/v2/cost'
        return self.get(url, params={'date': date, 'filter': filter_type})

    def get_ribao_profit(self, date):
        '''
        每个矿工的日收益
        '''
        url = '/ribao/v2/profit'
        return self.get(url, params={'date': date})

    def mine_overview(self, date):
        """
        获取MINING POOL损益概览
        :param date:
        :return:
        unitTReward:单t效益
        unitTPackingPledgeFee:单t质押(扇区)
        unitTPackingGasFee:单t gas(生产)
        """
        url = '/arockpool/asset/v1/overview?date={}'.format(date)
        data = {}
        params = {"date": date}
        return self.get(url=url, data=data, params=params)
