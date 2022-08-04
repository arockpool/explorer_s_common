import uuid
import json
import logging
import time
import datetime
import requests
import traceback
import base64
from urllib import parse
from elasticsearch import Elasticsearch

from explorer_s_common import debug, utils, consts, decorator
from explorer_s_common.mq.mq_kafka import Producer, MQ_TOPIC_SYS_ERROR


class BbheBase(object):

    def __init__(self):
        self.host = consts.BBHEHOST

    def get_headers(self):
        base64_secret = base64.b64encode(consts.BBHESECRET.encode("utf-8")).decode("utf-8")
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36',
            "Authorization": 'Basic ' + base64_secret
        }

    def fetch(self, url, params={}, data={}):
        try:
            logging.warning('url--> %s, params--> %s' % (url, params))
            result = requests.get(self.host + url, headers=self.get_headers(),
                                  params=params, data=data, timeout=100).json()
            # logging.warning('response--> %s' % result)
            if result.get('code', 500) not in (200, 1001) and not url.startswith('/v1/data/asset/all'):
                Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'bbhe',
                                                     'url': url, 'detail': result.get('message', '')})
            return result
        except Exception as e:
            detail = "params is: %s , post_data is: %s , detail is：%s " % (
                str(params), str(data), debug.get_debug_detail(e))
            # 发送kafka消息
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'bbhe', 'url': url, 'detail': detail})
            return {}

    def get_blocks(self, page_size=100, height=None):
        '''获取出块信息'''
        url = '/v1/data/blocks'
        return self.fetch(url=url, params={'page_size': page_size, 'height': height})

    def get_overview(self):
        '''获取概要信息'''
        url = '/v1/data/general'
        return self.fetch(url=url, params={})

    def get_miner_detail(self, miner_no):
        '''获取矿工详情'''
        url = '/v1/data/miner/' + miner_no
        return self.fetch(url=url, params={})

    def get_active_miners(self, page_index=0, page_size=100):
        '''获取活跃矿工'''
        url = '/v1/data/miner/active'
        return self.fetch(url=url, params={'page_index': page_index, 'page_size': page_size})

    def get_pool_miners(self):
        '''获取矿池矿工列表'''
        url = '/v1/data/miners'
        return self.fetch(url=url, params={})

    def get_net_stat(self, date):
        '''获取全网统计信息'''
        url = '/v1/data/asset/all/' + date
        return self.fetch(url=url, params={})

    def get_pool_stat(self, date):
        '''获取矿池统计信息'''
        url = '/v1/data/asset/arockpool/' + date
        return self.fetch(url=url, params={})

    def get_miner_stat(self, miner_no, date):
        '''获取矿池统计信息'''
        url = '/v1/data/asset/miner/%s/%s' % (miner_no, date)
        return self.fetch(url=url, params={})


class BbheEsBase(object):

    def __init__(self):
        self.es = Elasticsearch(
            # 连接集群，以列表的形式存放各节点的IP地址
            [consts.BBHEES_HOST],
            # 账号密码
            http_auth=(consts.BBHEES_USER, consts.BBHEES_PASSWORD),
            # 连接前测试
            sniff_on_start=False,
            # 节点无响应时刷新节点
            sniff_on_connection_fail=False,
            # 设置超时时间
            sniff_timeout=60,
            # 设置压缩
            http_compress=True,
            # 设置超时时间 有4次重试  超时重试也失败就会500
            timeout=30,
        )

    def fetch(self, index="", body={}, query_type='query',):
        try:
            logging.warning('index--> %s, body--> %s' % (index, body))
            if query_type == 'count':
                result = self.es.count(index=index, body=body).get('count', 0)
            elif query_type == 'aggs':
                result = self.es.search(index=index, body=body).get('aggregations')
            elif query_type == 'create_scroll':
                obj = self.es.search(index=index, body=body, scroll="5m")
                result = obj.get('hits')
                result["_scroll_id"] = obj.get("_scroll_id")
            else:
                result = self.es.search(index=index, body=body, timeout="60s").get('hits')
            # logging.warning('response--> %s' % result)
            return result
        except Exception as e:
            detail = "body is: %s , detail is：%s " % (str(body), debug.get_debug_detail(e))
            # 发送kafka消息
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'bbhe_es', 'url': index, 'detail': detail})
            return {}

    def scroll(self, scroll_id, scroll="5m"):
        try:
            obj = self.es.scroll(scroll=scroll, scroll_id=scroll_id)
            result = obj.get('hits')
            result["_scroll_id"] = obj.get("_scroll_id")
            return result
        except Exception as e:
            detail = "scroll, detail is：%s " % (debug.get_debug_detail(e),)
            # 发送kafka消息
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'bbhe_es', 'scroll_id': scroll_id, 'detail': detail})
            return {}

    def get_height_message(self, height):
        '''获取单个高度的所有消息'''
        query_json = {
            "query": {"term": {"height": {"value": height}}}, "from": 0, "size": 10000
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_message_count(self, miner_no=None, msg_ids=[], msg_method=None, is_transfer=False, start_height=None,
                          end_height=None, all=False):
        '''获取消息总数'''
        must_query = []
        if miner_no is not None:
            if all:
                must_query.append({"bool": {"should": [{"term": {
                    "msg_from": miner_no}},
                    {"term": {"msg_to": miner_no}}]
                }})
            else:
                must_query.append(
                    {"term": {"msg_to": {"value": miner_no}}}
                )
        if msg_method:
            must_query.append({"match": {"msg_method_name": msg_method}})
        if msg_ids:
            must_query.append({"terms": {"msg_cid": msg_ids}})
        if start_height and end_height:
            must_query.append({"range": {"height": {"gte": start_height, "lte": end_height}}})
        if is_transfer:
            must_query.append({"terms": {"msg_method_name": ["Send", "WithdrawBalance"]}})

        query_json = {"query": {"bool": {"must": must_query}}}
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type='count')

    def get_message_method_types(self, miner_no=None, msg_ids=[], is_transfer=False, start_height=None,
                                 end_height=None, all=False):
        '''获取消息总数'''
        must_query = []
        if miner_no is not None:
            if all:
                must_query.append({"bool": {"should": [{"term": {
                    "msg_from": miner_no}},
                    {"term": {"msg_to": miner_no}}]
                }})
            else:
                must_query.append(
                    {"term": {"msg_to": {"value": miner_no}}}
                )
        if msg_ids:
            must_query.append({"terms": {"msg_cid": msg_ids}})
        if start_height and end_height:
            must_query.append({"range": {"height": {"gte": start_height, "lte": end_height}}})
        if is_transfer:
            must_query.append({"terms": {"msg_method_name": ["Send", "WithdrawBalance"]}})
        query_json = {
            "size": 0,
            "aggs": {"msg_methods": {"terms": {"field": "msg_method_name", "size": 100}}},
            "query": {"bool": {"must": must_query, "must_not": [{"terms": {"msg_method_name": ["", "unkown"]}}]}}
        }

        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type='aggs')

    def get_message_list(self, is_next=False, miner_no=None, msg_method=None, msg_ids=[], start_height=None,
                         end_height=None, all=False, is_transfer=False, page_size=20, page_index=1):
        '''获取一个地址的所有消息'''
        must_query = []
        if is_transfer:
            must_query.append({"terms": {"msg_method_name": ["Send", "WithdrawBalance"]}})

        if miner_no is not None:
            if all:  # 包括发送和接收
                must_query.append(
                    {"bool": {"should": [{"term": {
                        "msg_from": miner_no}},
                        {"term": {"msg_to": miner_no}}]
                    }})
            else:
                must_query.append({"term": {"msg_to": {"value": miner_no}}})
        if msg_ids:
            must_query.append({"terms": {"msg_cid": msg_ids}})

        if msg_method:
            must_query.append({"match": {"msg_method_name": msg_method}})

        if start_height and end_height:
            must_query.append({"range": {"height": {"gte": start_height, "lte": end_height}}})
        query_json = {
            "_source": {
                "excludes": ["msg_params"]},
            "sort": [{"height": {"order": "desc"}}],
            "size": page_size
        }
        if must_query:
            query_json["query"] = {"bool": {"must": must_query}}
        if not is_next:
            query_json["from"] = (page_index - 1) * page_size
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json,
                          query_type="create_scroll" if is_next else 'query')

    def get_all_message_list(self, timestamp=0, is_next=False, miner_no=None, msg_ids=[], page_size=20, page_index=1):
        '''获取一个地址的所有消息,包括发送和接收'''
        if is_next:
            date_query = {"lt": timestamp}
        else:
            date_query = {"gt": timestamp}
        must_query = [{"range": {"synced_at": date_query}}]

        if miner_no is not None:
            must_query.append(
                {"bool": {"should": [{"term": {
                    "msg_from": miner_no}},
                    {"term": {"msg_to": miner_no}}]
                }})

        if msg_ids:
            must_query.append({"terms": {"msg_cid./": msg_ids}})

        query_json = {
            "query": {"bool": {"must": must_query}},
            "sort": [{"synced_at": {"order": "desc"}}],
            "from": (page_index - 1) * page_size, "size": page_size
        }
        return self.fetch(index='chainwatch-messages', body=query_json)

    def get_transfer_message_list(self, timestamp=0, is_next=False, miner_no=None, msg_ids=[], page_size=20,
                                  page_index=1):
        '''获取一个地址的转账,包括发送和接收'''
        if is_next:
            date_query = {"lt": timestamp}
        else:
            date_query = {"gt": timestamp}
        must_query = [{"range": {"synced_at": date_query}}, {"match": {"msg_method_name": "Send"}}]

        if miner_no is not None:
            must_query.append(
                {"bool": {"should": [{"term": {
                    "msg_from": miner_no}},
                    {"term": {"msg_to": miner_no}}]
                }})

        if msg_ids:
            must_query.append({"terms": {"msg_cid./": msg_ids}})

        query_json = {
            "query": {"bool": {"must": must_query}},
            "sort": [{"synced_at": {"order": "desc"}}],
            "from": (page_index - 1) * page_size, "size": page_size
        }
        return self.fetch(index='chainwatch-messages', body=query_json)

    def get_transfer_message_count(self, miner_no=None, msg_ids=[]):
        '''获取一个地址的转账,包括发送和接收'''
        must_query = [{"match": {"msg_method_name": "Send"}}]

        if miner_no is not None:
            must_query.append(
                {"bool": {"should": [{"term": {
                    "msg_from": miner_no}},
                    {"term": {"msg_to": miner_no}}]
                }})

        if msg_ids:
            must_query.append({"terms": {"msg_cid./": msg_ids}})

        query_json = {
            "query": {"bool": {"must": must_query}}}
        return self.fetch(index='chainwatch-messages', body=query_json, query_type="count")

    def get_all_message_count(self, miner_no=None, msg_method=None):
        '''获取消息总数'''
        must_query = []
        if miner_no is not None:
            must_query.append({"bool": {"should": [{"term": {
                "msg_from": miner_no}},
                {"term": {"msg_to": miner_no}}]
            }})
        if msg_method:
            must_query.append({"terms": {"msg_method_name": msg_method}})
        query_json = {"query": {"bool": {"must": must_query}}}
        return self.fetch(index='chainwatch-messages', body=query_json, query_type='count')

    def get_memory_pool_message(self, page_size=20, page_index=1):
        '''获取内存池消息'''
        query_json = {
            "from": (page_index - 1) * page_size, "size": page_size
        }
        return self.fetch(index='chainwatch-mpool_message', body=query_json)

    def get_message_detail(self, msg_cid):
        '''
        获取单个消息
        '''
        query_json = {
            "query": {"term": {"msg_cid": {"value": msg_cid}}}
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_block_detail(self, block_id):
        '''获取block消息'''
        query_json = {
            "query": {"term": {"cid": {"value": block_id}}}
        }
        return self.fetch(index='chainwatch-blocks', body=query_json)

    def get_block_message(self, block_id):
        '''获取block消息'''
        query_json = {
            "query": {"term": {"block": {"value": block_id}}}, "from": 0, "size": 10000
        }
        return self.fetch(index='chainwatch-block_messages', body=query_json)

    def get_block_by_message_id(self, message_id):
        '''获取blockid通过message_id'''
        query_json = {
            "query": {"term": {"message": {"value": message_id}}}, "from": 0, "size": 10
        }
        return self.fetch(index='chainwatch-block_messages', body=query_json)

    def get_deal_by_sync_timestamp(self, timestamp):
        '''根据同步时间戳获取订单列表'''
        query_json = {
            "query": {"range": {"SyncedAt": {"gte": timestamp}}}, "from": 0, "size": 10000
        }
        return self.fetch(index='chainwatch-dealinfo', body=query_json)

    def get_update_deal(self, height):
        '''获取更新的订单列表'''
        query_json = {
            "query": {"bool": {"should": [
                {"range": {"SectorStartEpoch": {"gte": height}}},
                {"range": {"LastUpdatedEpoch": {"gte": height}}},
                {"range": {"SlashEpoch": {"gte": height}}}
            ]}}, "from": 0, "size": 10000
        }
        return self.fetch(index='chainwatch-dealinfo', body=query_json)

    def get_increase_deal(self, height):
        '''获取增量订单列表'''
        query_json = {
            "query": {"bool": {"must": [
                {"term": {"SectorStartEpoch": {"value": -1}}},
                {"term": {"LastUpdatedEpoch": {"value": 0}}},
                {"term": {"SlashEpoch": {"value": -1}}},
                {"range": {"StartEpoch": {"gte": height}}}
            ]}}, "from": 0, "size": 10000
        }
        return self.fetch(index='chainwatch-dealinfo', body=query_json)

    def get_index_overview(self, height):
        '''根据高度获取指数概览'''
        query_json = {
            "query": {"term": {"Height": {"value": height}}}, "from": 0, "size": 1000
        }
        return self.fetch(index='chainwatch-overview', body=query_json)

    def get_deal_stat(self):
        '''根据高度获取指数概览'''
        query_json = {
            "aggs": {
                "deal_count": {"value_count": {"field": 'PieceSize'}},
                "deal_size": {"sum": {"field": 'PieceSize'}}
            }, "size": 0
        }
        return self.fetch(index='chainwatch-dealinfo', body=query_json, query_type="aggs")

    def get_miner_gas_cost_stat(self, msg_method, start_height, end_height, miner_no=None):
        '''获取指定时间段矿工gas消耗统计'''
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gte": start_height, "lt": end_height}}},
                {"terms": {"msg_method": msg_method}}
            ]}},
            "aggs": {"miner_group": {
                "terms": {"field": "msg_to", "size": 10000, "order": {"gas_sum": "desc"}},
                "aggs": {"gas_sum": {"sum": {"field": "gascost_total_cost"}}}
            }}, "size": 0
        }
        if miner_no:
            query_json['query']['bool']['filter'].append({"term": {"msg_to": miner_no}})
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type="aggs")

    def get_miner_gas_cost_stat_2(self, msg_method_name, start_height, end_height, miner_no=None):
        '''根据方法名字 获取指定时间段矿工gas消耗统计'''
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gte": start_height, "lt": end_height}}},
                {"terms": {"msg_method_name": msg_method_name}}
            ]}},
            "aggs": {"miner_group": {
                "terms": {"field": "msg_to", "size": 10000, "order": {"gas_sum": "desc"}},
                "aggs": {"gas_sum": {"sum": {"field": "gascost_total_cost"}}}
            }}, "size": 0
        }
        if miner_no:
            query_json['query']['bool']['filter'].append({"term": {"msg_to": miner_no}})
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type="aggs")

    def get_gas_cost_stat_by_miner_no(self, miner_no, msg_method, start_height, end_height, is_stat=False,
                                      sector_size=None):
        '''根据矿工ID获取指定时间段矿工gas消耗统计'''
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gte": start_height, "lt": end_height}}}
            ]}},
            "aggs": {"miner_group": {
                "terms": {"field": "msg_method", "size": 20},
                "aggs": {"gas_sum": {"sum": {"field": "gascost_total_cost"}},
                         "pledge_sum": {"sum": {"field": "msg_value"}}}
            }}, "size": 0
        }
        if miner_no:
            query_json["query"]["bool"]["filter"].append({"term": {"msg_to": miner_no}})
        if sector_size:
            query_json["query"]["bool"]["filter"].append({"term": {"sector_size": sector_size}})
        if msg_method:
            query_json["query"]["bool"]["filter"].append({"terms": {"msg_method": msg_method}})
        if is_stat:
            query_json["aggs"]["gas_sum_total"] = {"sum": {"field": "gascost_total_cost"}}
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type="aggs")

    def get_148888_active_miners(self):
        '''获取148888高度的矿工信息'''
        query_json = {"from": 0, "size": 10000}
        return self.fetch(index='chainwatch-miner148888', body=query_json)

    def get_height_gas_cost_stat(self, msg_method, start_height, end_height):
        '''获取指定时间段矿工gas消耗统计'''
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gte": start_height, "lt": end_height}}},
                {"terms": {"msg_method": msg_method}}
            ]}},
            "aggs": {"height_group": {
                "terms": {"field": "height", "size": 10000, "order": {"_key": "asc"}},
                "aggs": {"gas_sum": {"sum": {"field": "gascost_total_cost"}}}
            }}, "size": 0
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type="aggs")

    def get_height_gas_cost_stat_2(self, msg_method_name, start_height, end_height):
        '''根据方法名字 获取指定时间段矿工gas消耗统计'''
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gte": start_height, "lt": end_height}}},
                {"terms": {"msg_method_name": msg_method_name}}
            ]}},
            "aggs": {"height_group": {
                "terms": {"field": "height", "size": 10000, "order": {"_key": "asc"}},
                "aggs": {"gas_sum": {"sum": {"field": "gascost_total_cost"}}}
            }}, "size": 0
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type="aggs")

    def get_pool_miner_detail(self, miner_no):
        '''查询矿池miner详情(从每日矿工数据中获取)'''
        query_json = {
            "query": {"term": {"miner_id": {"value": miner_no}}}, "sort": [{"synced_at": {"order": "desc"}}]
        }
        return self.fetch(index='chainwatch-arockpool_miner', body=query_json)

    def get_pool_miner_wallet_detail(self, miner_no):
        '''查询矿池miner钱包地址'''
        query_json = {
            "query": {"term": {"miner_id": {"value": miner_no}}}, "sort": [{"synced_at": {"order": "desc"}}]
        }
        return self.fetch(index='chainwatch-arockpool_wallet', body=query_json)

    def get_pool_attention_miner_detail(self, miner_no):
        '''查询矿池miner详情(从活跃矿工数据中获取)'''
        query_json = {
            "query": {"term": {"miner_id": {"value": miner_no}}}, "sort": [{"synced_at": {"order": "desc"}}]
        }
        return self.fetch(index='chainwatch-miner', body=query_json)

    def get_miner_info_by_address(self, miner_address):
        """
        获得矿工详情,根据4个钱包的长短地址进行查询
        :param miner_address:钱包地址
        :return:
        """
        # 取2天的数据,防止当日没有数据
        day_time = int(time.mktime((datetime.date.today() - datetime.timedelta(days=1)).timetuple()))
        query_json = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"synced_at": {"gte": day_time}}},
                        {"bool": {"should": [{"term": {"worker_id": miner_address}},
                                             {"term": {"worker_address": miner_address}},
                                             {"term": {"miner_id": miner_address}},
                                             {"term": {"address": miner_address}},
                                             {"term": {"owner_id": miner_address}},
                                             {"term": {"owner_address": miner_address}},
                                             {"term": {"poster_id": miner_address}},
                                             {"term": {"post_address": miner_address}}
                                             ]}}]}},
            "sort": [{"synced_at": {"order": "desc"}}]}

        return self.fetch(index='chainwatch-arockpool_miner', body=query_json)

    def get_miner_wallet_by_address_list(self, address_list):
        """
        获得钱包详情,根据4个钱包的长短地址进行查询
        :param address_list:钱包地址
        :return:
        """
        # 取2天的数据,防止当日没有数据
        query_json = {
            "size": 10000,
            "query": {
                "bool": {
                    "must": [
                        {"bool": {"should": [{"terms": {"worker_id": address_list}},
                                             {"terms": {"worker_address": address_list}},
                                             {"terms": {"miner_id": address_list}},
                                             {"terms": {"address": address_list}},
                                             {"terms": {"owner_id": address_list}},
                                             {"terms": {"owner_address": address_list}},
                                             {"terms": {"poster_id": address_list}},
                                             {"terms": {"post_address": address_list}}
                                             ]}}]}},
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index='chainwatch-arockpool_wallet', body=query_json)

    def get_is_miner(self, data, index='chainwatch-arockpool_miner'):
        '''查询是否为矿工'''
        query_json = {
            "query": {
                "multi_match": {
                    "query": data,
                    "fields": ["miner_id", "address", "owner_id", "worker_id", "owner_address", "post_address",
                               "worker_address", "poster_id"],
                    "type": "best_fields"
                }
            },
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index=index, body=query_json)

    def get_is_block_hight(self, data):
        '''查询是否为区块高度'''
        query_json = {
            "query": {
                "multi_match": {
                    "query": data,
                    "fields": ["height"],
                    "type": "best_fields"
                }
            },
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index='chainwatch-block_messages', body=query_json)

    def get_is_block(self, data):
        '''查询是否为区块'''
        query_json = {
            "query": {
                "multi_match": {
                    "query": data,
                    "fields": ["block"],
                    "type": "best_fields"
                }
            },
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index='chainwatch-block_messages', body=query_json)

    def get_is_message(self, data):
        '''查询是否为消息'''
        query_json = {
            "query": {
                "multi_match": {
                    "query": data,
                    "fields": ["msg_cid"],
                    "type": "best_fields"
                }
            },
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_is_miner_owner(self, data):
        """
        查询是否为矿工(miner_no,address)
        """
        query_json = {
            "query": {
                "multi_match": {
                    "query": data,
                    "fields": ["miner_id", "address", ],
                    "type": "best_fields"
                }
            },
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index='chainwatch-arockpool_miner', body=query_json)

    def get_is_miner_wallet(self, data):
        """
        查询是否为矿工(miner_no,address)
        """
        query_json = {
            "query": {
                "multi_match": {
                    "query": data,
                    "fields": ["owner_id", "worker_id", "owner_address", "post_address",
                               "worker_address", "poster_id"],
                    "type": "best_fields"
                }
            },
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index='chainwatch-arockpool_miner', body=query_json)

    def get_miner_wallet_value(self, data):
        """
        查询是否为矿工(miner_no,address)
        """
        query_json = {
            "query": {
                "multi_match": {
                    "query": data,
                    "fields": ["owner_id", "worker_id", "owner_address", "post_address",
                               "worker_address", "poster_id"],
                    "type": "best_fields"
                }
            },
            "sort": [{"synced_at": {"order": "desc"}}]}
        return self.fetch(index='chainwatch-arockpool_wallet', body=query_json)

    def get_miner_wallet_change(self, miner_no, balance_value, start_time):
        """
        钱包变化值
        """
        query_json = {
            "query": {"bool": {
                "must": [{"range": {"synced_at": {"gte": start_time}}},
                         {"range": {"msg_value": {"gt": balance_value}}},
                         {"terms": {"msg_method_name": ["Send", "WithdrawBalance"]}},
                         {"bool": {"should": [{"term": {
                             "msg_from": miner_no}},
                             {"term": {"msg_to": miner_no}}]
                         }}
                         ]}},
            "_source": {
                "excludes": ["msg_params"]},
            "sort": [{"height": {"order": "desc"}}],
            "size": 20
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_line(self, data_type, miner_no, start_time, end_time):
        """
        钱包走势图
        """
        query_json = {"query": {"bool": {
            "must": [{"range": {"synced_at": {
                "gte": start_time,
                "lte": end_time}}},
                {"match": {data_type: miner_no}}]}},
            "sort": [{"synced_at": {"order": "desc"}}],
            "size": 100}

        return self.fetch(index='chainwatch-arockpool_wallet', body=query_json)

    def get_filter_message_list(self, timestamp=0, is_next=False, miner_address=None, page_size=20,
                                page_index=1, methods=[], direction=None):
        '''根据方法过滤,获得消息列表'''
        if is_next:
            date_query = {"lt": timestamp}
        else:
            date_query = {"gt": timestamp}
        method_list = []
        for method in methods:
            method_list.append({"match_phrase": {"msg_method_name": method}})
        must_query = [{"bool": {"should": method_list}},
                      {"match": {direction: miner_address}},
                      {"range": {"synced_at": date_query}}]

        query_json = {
            "query": {"bool": {"must": must_query}},
            "sort": [{"synced_at": {"order": "desc"}}],
            "from": (page_index - 1) * page_size, "size": page_size
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_filter_message_count(self, methods, miner_address, direction):
        '''根据方法过滤,获取消息总数'''

        method_list = []
        for method in methods:
            method_list.append({"match_phrase": {"msg_method_name": method}})
        must_query = [{"bool": {"should": method_list}},
                      {"match": {direction: miner_address}}]
        query_json = {"query": {"bool": {"must": must_query}}}

        return self.fetch(index='chainwatch-messages', body=query_json, query_type='count')

    def get_cost_message_value_merge(self, start_timestamp, end_timestamp, miner_address, methods, direction):
        '''根据方法过滤,获得消息列表'''
        date_query = {"lt": end_timestamp, "gte": start_timestamp}
        method_list = []
        for method in methods:
            method_list.append({"match_phrase": {"msg_method_name": method}})
        must_query = [{"bool": {"should": method_list}},
                      {"match": {direction: miner_address}},
                      {"range": {"height": date_query}}]

        query_json = {
            "query": {"bool": {"must": must_query}},
            "sort": [{"height": {"order": "desc"}}],
            "size": 10000
        }
        return self.fetch(index='chainwatch-messages', body=query_json)

    def get_transfer_list(self, msg_from, msg_to, height_gte=None):
        """
        :param msg_from: 转出账户
        :param msg_to: 转入账户
        :param height_gte: 开始区块高度
        :return:
        """
        must_query = [{"term": {"msg_from": {"value": msg_from}}}, {"term": {"msg_to": {"value": msg_to}}}, ]
        if height_gte:
            must_query.append({"range": {"height": {"gte": height_gte}}})
        query_json = {"query": {"bool": {"must": must_query}}, "size": 100}

        return self.fetch(index='chainwatch-messages', body=query_json)

    def get_deal_detail(self, deal_id):
        """
        查询deal详情
        """
        query_json = {"query": {"match": {"DealID": deal_id}}}
        return self.fetch(index='chainwatch-dealinfo', body=query_json)

    def get_deal_message(self, deal_id):
        """
        根据deal的PieceCID,查询所在的消息
        数据更新,使用 msg_return 进行查询  其中包含订单号,更加的精确
        :param deal_id:
        :return:
        """
        # query_json = {"query": {"match_phrase": {"msg_params": PieceCID}}}
        # query_json = {"query": {"bool": {"must": [
        #     {"match_phrase": {"msg_params": PieceCID}},
        #     {"match_phrase": {"msg_params": provider}}]}}}
        query_json = {"query": {"match_phrase": {"msg_return": deal_id}}}

        return self.fetch(index='chainwatch-messages', body=query_json)

    def get_height_messages(self, heights=[], source=["msg_method", "msg_to", "gascost_total_cost", "msg_params", "height",
                                                      "sector_count", "base_fee", "msg_value", "base_fee2", "msgrct_exit_code"]):
        '''获取多个高度的所有消息'''
        query_json = {
            "query": {"terms": {"height": heights}}, "from": 0, "size": 10000, "_source": source
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_msg_value(self, height):
        """获取每日msg_value"""
        query_json = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "height": {
                                    "gte": height - 2880,
                                    "lt": height
                                }
                            }
                        },

                        {
                            "terms": {
                                "msg_method_name": [
                                    "Send"
                                ]
                            }
                        }
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "sector_group": {
                    "terms": {
                        "field": "msg_method_name",
                        "size": 10
                    },
                    "aggs": {
                        "gas_sum": {
                            "sum": {
                                "field": "msg_value"
                            }
                        }
                    }
                }
            }
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type='aggs')

    def get_messages_stat_by_miner_no(self, miner_no, msg_method, start_height, end_height):
        '''根据矿工ID获取指定时间段消息数量和成功消息数量统计'''
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gte": start_height, "lt": end_height}}},
                {"terms": {"msg_method": msg_method}},
                {"term": {"msg_to": miner_no}}
            ]}},
            "aggs": {"miner_group": {
                "terms": {"field": "msg_method_name", "size": 5},
                "aggs": {"msg_status": {"terms": {"field": "msgrct_exit_code", "size": 2}}}
            }}, "size": 0
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type="aggs")

    def get_messages_stat_others_by_miner_no(self, miner_no, msg_method, start_height, end_height):
        '''根据矿工ID获取指定时间段消息数量和成功消息数量统计'''
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gte": start_height, "lt": end_height}}},
                {"bool": {"must_not": [{"terms": {"msg_method": msg_method}}]}},
                {"term": {"msg_to": miner_no}}
            ]}},
            "aggs": {"msg_status": {"terms": {"field": "msgrct_exit_code", "size": 2}}},
            "size": 0
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json, query_type="aggs")

    def get_messages_deal_list(self, start_height):
        """从消息中获取订单列表"""
        query_json = {
            "query": {"bool": {"filter": [
                {"range": {"height": {"gt": start_height}}},
                {"term": {"msg_method": {"value": 4}}},
                {"exists": {"field": "msg_return"}}
            ]}},
            "size": 10000,
            "sort": [{"synced_at": {"order": "asc"}}]
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_height_messages_back(self, height):
        '''获取单个高度的所有消息'''
        query_json = {
            "query": {"term": {"height": {"value": height}}}, "from": 0, "size": 10000
        }
        return self.fetch(index='chainwatch-messages-zone-2020,chainwatch-messages-zone-2021,chainwatch-messages-zone-2022', body=query_json)

    def get_block_by_message_ids(self, message_ids):
        '''获取blockid通过message_id'''
        query_json = {
            "query": {"terms": {"message": message_ids}}, "from": 0, "size": 10000
        }
        return self.fetch(index='chainwatch-block_messages', body=query_json)

    def get_height_arockpool_wallet(self, search_after=[], height=None):
        '''获取单个高度的所有消息'''
        query_json = {
            "size": 2000,
            "from": 0,
            "sort": [{"height": {"order": "asc"}}, {"_id": {"order": "asc"}}]}
        if search_after:
            query_json["search_after"] = search_after
        if height:
            query_json["query"] = {"range": {"height": {"gte": height}}}
        return self.fetch(index='chainwatch-arockpool_wallet', body=query_json)
