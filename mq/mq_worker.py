import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(BASE_DIR))

import json
import logging
import signal
import datetime
import requests
from urllib import parse
from functools import wraps

from kafka.errors import NoBrokersAvailable

from explorer_s_common import debug, consts, utils, inner_server
from mq_kafka import *

logging.basicConfig(
    format='%(levelname)s:%(asctime)s %(pathname)s--%(funcName)s--line %(lineno)d-----%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)


def log_worker(func):
    '''
    记录操作流水
    '''

    @wraps(func)
    def wrapper(*args, **kwargs):

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            debug.get_debug_detail(e)
            result = [99904, '系统错误']

        logging.warning("方法：%s，参数：%s，返回值：%s" % (
            func.__name__,
            args[1] if len(args) > 1 else None,
            result
        ))

        try:
            # 如果操作出错
            if result and result[0] != 0:
                logging.warning("记录错误信息")

        except Exception as e:
            print(e)

        return result

    return wrapper


class Worker(object):

    def __init__(self):
        self.MQ_DICT = {
            'slow_request': {'topic': MQ_TOPIC_SLOW_REQUEST, 'group': MQ_GROUP_SYSTEM},
            'sys_error': {'topic': MQ_TOPIC_SYS_ERROR, 'group': MQ_GROUP_SYSTEM},
            'request_log': {'topic': MQ_TOPIC_REQUEST_LOG, 'group': MQ_GROUP_SYSTEM},
            'send_sms': {'topic': MQ_TOPIC_SEND_SMS, 'group': MQ_GROUP_SYSTEM},
            'send_email': {'topic': MQ_TOPIC_SEND_EMAIL, 'group': MQ_GROUP_SYSTEM},
        }

    def worker(self, method):
        """
        具体的执行消费者程序
        :param method: 具体需要执行的方法,在类中的其他三个方法中
        :return:
        """
        logging.warning("worker开启...")

        if not hasattr(self, method):
            logging.warning("找不到对应的worker")
            return

        if method not in self.MQ_DICT.keys():
            logging.warning("找不到对应的配置信息")
            return

        try:
            # 实例化消费者,从队列中取出消息
            consumer = Consumer(self.MQ_DICT[method]['topic'], self.MQ_DICT[method]['group'])
            for message in consumer.consumer:
                # 获取消息,将消息通过类型,发送到
                getattr(self, method)(message.value)
        except NoBrokersAvailable as e:
            logging.warning('kafka服务不可用...')
            sys.exit(0)

    @log_worker
    def slow_request(self, data):
        '''
        添加慢请求
        '''
        url = data.get("url")
        duration = float(data.get("duration", "0"))
        ip = data.get("ip")
        post_data = data.get("post_data")

        return inner_server.add_slow_request(request_url=url, duration=duration, ip=ip, post_data=post_data)

    @log_worker
    def sys_error(self, data):
        '''
        记录系统错误
        '''
        service = data.get("service")
        url = data.get("url")
        detail = data.get("detail")

        return inner_server.add_sys_error(service=service, request_url=url, detail=detail)

    @log_worker
    def request_log(self, data):
        '''
        添加请求日志
        '''
        return inner_server.add_request_log(data=data)

    @log_worker
    def send_sms(self, data):
        '''
        发送短信
        '''
        return inner_server.send_sms(data=data)

    @log_worker
    def send_email(self, data):
        '''
        发送邮件
        '''
        return inner_server.send_email(data=data)


def handle_hup(sig, frame):
    logging.warning("worker关闭...")
    sys.exit(0)


def handle_int(sig, frame):
    logging.warning("worker关闭...")
    sys.exit(0)


if __name__ == '__main__':

    if len(sys.argv) <= 1:
        logging.warning("worker未指定")
    else:
        signal.signal(signal.SIGINT, handle_int)
        signal.signal(signal.SIGHUP, handle_hup)
        worker = Worker()
        method = sys.argv[1]
        worker.worker(method)
