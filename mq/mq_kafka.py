import json
import os

from kafka import KafkaProducer, KafkaConsumer

# 消息队列的 topic
MQ_SERVERS = [os.getenv("KAFKA_SERVERS", ""), ]

MQ_TOPIC_SLOW_REQUEST = "explorer_slow_request"                  # 慢查询
MQ_TOPIC_SYS_ERROR = "explorer_sys_error"                        # 系统错误
MQ_TOPIC_REQUEST_LOG = "explorer_request_log"                    # 调用日志
MQ_TOPIC_SEND_SMS = "explorer_send_sms"                          # 发送短信
MQ_TOPIC_SEND_EMAIL = "explorer_send_email"                      # 发送邮件

MQ_GROUP_SYSTEM = 'explorer_g_system'                            # 系统服务分组


class Producer(object):

    def __init__(self):
        if os.getenv("DEVCODE", "dev") == "dev":  # 本地不发消息
            return
        self.producer = KafkaProducer(
            bootstrap_servers=MQ_SERVERS, api_version=(2, 4, 1),
            # 定义编码方式
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )

    def send(self, topic, data):
        if not topic or not data:
            return
        if os.getenv("DEVCODE", "dev") == "dev":  # 本地不发消息
            return
        self.producer.send(topic, data)
        self.producer.flush()


class Consumer(object):

    def __init__(self, topic, group_id=None):
        self.consumer = KafkaConsumer(
            topic, group_id=group_id, bootstrap_servers=MQ_SERVERS, api_version=(2, 4, 1),
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
