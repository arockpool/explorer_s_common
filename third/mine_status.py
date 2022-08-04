import logging

import requests
import json
from datetime import datetime, timedelta

# 当前机器状态
from explorer_s_common.cache import connect_redis, CACHE_SERVER
from explorer_s_common import debug


class MineStatus(object):
    def __init__(self, date_time=None):
        """

        :param source: 需要请求的资源,根据source_url的键命名
        :param date_time:获取的时间,字符串类型
        """
        self.base_url = r'https://lotus.tudouip.com'
        self.source_url = {
            "now": "/v1/third/worker/exceptional/list",  # 当前异常机器
            "yesterday_abnormal": "/v1/third/worker/exceptional/duration",  # 昨日机器异常时长
            "add": "/v1/third/worker/list"  # 新增机器列表
        }
        self.date_time = date_time

    def _get_source_url(self, source):
        return self.source_url[source]

    def _get_json_data(self, json_data, source):

        if source == "add":
            if self.date_time is None:
                start_date = "1970-01-01 00:00:00"
            else:
                start_date = self.date_time
            json_data['start_date'] = start_date
        return json_data

    def run(self, source, page_index=1, page_size=10, **kwargs):
        json_data = {"page_index": page_index, "page_size": page_size, **kwargs}
        url = self._get_source_url(source)
        json_data = self._get_json_data(json_data, source)
        # func = eval("self._get_result_{}".format(self.source))
        return json.loads(requests.post(url=self.base_url + url, json=json_data).content.decode())

    # def _get_result_now(self, url, json_data):
    #     """
    #     获取实时机器状态,定时任务,暂时不做过期时间处理,如果获取失败,那么使用上一次的数据
    #     :param url: 请求的url
    #     :param json_data: 请求体json数据
    #     :return:
    #     """
    #     return json.loads(requests.post(url=self.base_url + url, json=json_data).content.decode())
    #
    # def _get_result_yesterday_abnormal(self, url, json_data):
    #     """
    #     获得机器昨日异常时长,仅获得第一页数据
    #     :return list ->[{'err_time': 191.58, 'sn': 'CD01-G017-P1P2-5.61'},..]
    #     """
    #     return json.loads(requests.post(url=self.base_url + url, json=json_data).content.decode())
    #
    # def _get_result_add(self, url, json_data):
    #     """
    #     获得机器新增的机器信息
    #     :return list->[{'sn': 'CD01-G017-M2-3.61', 'code': '星矢一号-子Miner', 'join_date': '2020-09-17 18:27:26'},...]
    #     """
    #     return self._get_result_yesterday_abnormal(url, json_data)

    def mine_error_count_or_all_count(self, source):
        """
        通过第一个接口获得异常矿机数,通过第三个接口获得矿机总数,根据传入的source决定
        不需要json
        :return:异常机器的数量
        """
        url = self._get_source_url(source)
        json_data = {"page_index": 1, "page_size": 10}
        response = json.loads(requests.post(url=self.base_url + url, json=json_data).content.decode())
        return int(response['data']['total_count'])


if __name__ == '__main__':
    mine = MineStatus()
    # mine = MineStatus(source="add", date_time="2020-09-25 12:12:12")
    result = mine.run(source="yesterday_abnormal")
    print(result)
