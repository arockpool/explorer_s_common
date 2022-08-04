import base64
import logging
import requests
from explorer_s_common import debug, consts
from explorer_s_common.mq.mq_kafka import Producer, MQ_TOPIC_SYS_ERROR


class BbheChainBase(object):
    def __init__(self):
        self.host = consts.BBHEFILLOTUS_HOST

    @staticmethod
    def get_headers():
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36',
        }
        if consts.BBHESECRET:
            base64_secret = base64.b64encode(consts.BBHESECRET.encode("utf-8")).decode("utf-8")
            headers['Authorization'] = 'Basic ' + base64_secret
        return headers

    def fetch(self, url, params={}, data={}):
        try:
            logging.warning('url--> %s, params--> %s' % (url, params))
            result = requests.get(self.host + url, headers=self.get_headers(), params=params, data=data,
                                  timeout=100).json()
            # logging.warning('response--> %s' % result)
            if result.get('code', 500) != 200:
                Producer().send(MQ_TOPIC_SYS_ERROR,
                                {'service': 'bbhe', 'url': url, 'detail': result.get('message', '')})
            return result
        except Exception as e:
            detail = "params is: %s , post_data is: %s , detail is：%s " % (
                str(params), str(data), debug.get_debug_detail(e))
            # 发送kafka消息
            Producer().send(MQ_TOPIC_SYS_ERROR, {'service': 'bbhe', 'url': url, 'detail': detail})
            return {}

    def verify_signature(self, address, sign_bytes):
        path = '/lotus/wallet/verify'
        params = {
            'addr': address,
            'msg': '5369676e617475726520666f722066696c666f780a66303132373539350a323032312d30352d31345431313a30373a33312e3833355a',
            'sig_bytes': sign_bytes
        }
        return self.fetch(path, params)

    def address_to_miner_no(self, address):
        path = '/lotus/state/lookup'
        params = {
            'addr': address
        }
        return self.fetch(path, params)


if __name__ == '__main__':
    bhc = BbheChainBase()
    #     r = bhc.address_to_miner_no('f2jqzjetdv54mpf6crni75tp3wvgjbuesrapuz4pq')
    #     print(r)
    r = bhc.verify_signature('f3qjln67txncfoureifue3gqqze7uzl6r4ktl2lqzjbsuqwzxiynrkbbda3ugbw6w4t6vqrhl6hcqynqgfydoa', '02ab0454ef18c62117345353d39808f032d06d3c663a64053c82fa3cad8e708cb790a54dab13c50c412eedded77d61fb470baa5666928b5a6bf3a129f29f70b2140add38210462a286d59dffdf7aa73d10830f824d2034aea99cacc2caedc3c319')
    print(r)
