import os
import time
import string
import random
import hashlib
import requests
import logging

logging.basicConfig(
    format='%(levelname)s:%(asctime)s %(pathname)s--%(funcName)s--line %(lineno)d-----%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)

try:
    from lxml import etree
except ImportError:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

from zg_s_common import consts
from zg_s_common.weixin import config

FAIL = "FAIL"
SUCCESS = "SUCCESS"


class WeixinPay(object):

    def __init__(self, sandbox=False, app_key='codoonhealth_app'):
        self.app_key = app_key if app_key else 'codoonhealth_app'
        self.app_id = config.DICT_WEIXIN_APP[self.app_key]['app_id']
        self.mch_id = config.DICT_WEIXIN_APP[self.app_key]['mch_id']
        self.mch_key = config.DICT_MCH[self.mch_id]
        self.notify_url = "https://api.%s/mall/api/weixinpaynotify" % (consts.MAIN_DOMAIN)
        self.sess = requests.Session()
        self.weixinpay_domain = "https://api.mch.weixin.qq.com"
        self.sandbox = sandbox

    @property
    def nonce_str(self):
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(32))

    def sign(self, raw):
        raw = [(k, str(raw[k]) if isinstance(raw[k], int) else raw[k])
               for k in sorted(raw.keys())]
        s = "&".join("=".join(kv) for kv in raw if kv[1])
        s += "&key={0}".format(self.mch_key)
        return hashlib.md5(s.encode("utf-8")).hexdigest().upper()

    def check(self, data):
        sign = data.pop("sign")
        return sign == self.sign(data)

    def to_xml(self, raw):
        s = ""
        for k, v in raw.items():
            s += "<{0}>{1}</{0}>".format(k, v)
        s = "<xml>{0}</xml>".format(s)
        return s.encode("utf-8")

    def to_dict(self, content):
        raw = {}
        try:
            root = etree.fromstring(content, etree.XMLParser(resolve_entities=False))
            for child in root:
                raw[child.tag] = child.text
        except Exception as e:
            pass

        return raw

    def get_sandbox_key(self):

        data = {
            'mch_id': self.mch_id,
            'nonce_str': self.nonce_str,
        }
        data['sign'] = self.sign(data)

        resp = requests.post(
            "https://api.mch.weixin.qq.com/sandboxnew/pay/getsignkey",
            data=self.to_xml(data)
        )
        content = resp.content.decode("utf-8")
        self.mch_key = self.to_dict(content)['sandbox_signkey']
        print('self.mch_key=>', self.mch_key)

    def _fetch(self, url, data):

        if self.sandbox:
            self.get_sandbox_key()
            url = self.weixinpay_domain + '/sandboxnew' + url
        else:
            url = self.weixinpay_domain + url

        data.setdefault("appid", self.app_id)
        data.setdefault("mch_id", self.mch_id)
        data.setdefault("nonce_str", self.nonce_str)
        data.setdefault("sign", self.sign(data))

        resp = self.sess.post(url, data=self.to_xml(data))
        content = resp.content.decode("utf-8")

        if "return_code" in content:
            data = self.to_dict(content)
            if data['return_code'] == FAIL:
                logging.error(data['return_msg'])
            return data
        return content

    def reply(self, msg, ok=True):
        code = SUCCESS if ok else FAIL
        return self.to_xml(dict(return_code=code, return_msg=msg))

    def unified_order(self, body, out_trade_no, total_fee,
                      spbill_create_ip="127.0.0.1", trade_type="APP", openid=None):
        """
        统一下单
        out_trade_no、body、total_fee、trade_type必填
        app_id, mchid, nonce_str自动填写
        spbill_create_ip 在flask框架下可以自动填写, 非flask框架需要主动传入此参数
        """
        url = "/pay/unifiedorder"

        data = {
            'body': body,
            'out_trade_no': out_trade_no,
            'total_fee': total_fee,
            'spbill_create_ip': spbill_create_ip,
            'trade_type': trade_type,
            'notify_url': self.notify_url
        }

        if openid:
            data.update({'openid': openid})

        return self._fetch(url, data)

    def app(self, body, out_trade_no, total_fee):
        raw = self.unified_order(body, out_trade_no, total_fee, trade_type="APP")

        data = {
            'appid': self.app_id,
            'partnerid': self.mch_id,
            'prepayid': raw["prepay_id"],
            'package': 'Sign=WXPay',
            'noncestr': self.nonce_str,
            'timestamp': str(int(time.time()))
        }
        data['sign'] = self.sign(data)
        return data

    def jsapi(self, body, out_trade_no, total_fee, openid):
        """
        生成给JavaScript调用的数据
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=7_7&index=6
        """
        # kwargs.setdefault("trade_type", "JSAPI")
        raw = self.unified_order(body, out_trade_no, total_fee, trade_type="JSAPI", openid=openid)
        package = "prepay_id={0}".format(raw["prepay_id"])

        data = {
            'appId': self.app_id,
            'timeStamp': str(int(time.time())),
            'nonceStr': self.nonce_str,
            'package': package,
            'signType': 'MD5'
        }
        data['sign'] = self.sign(data)
        return data

    def order_query(self, **data):
        """
        订单查询
        out_trade_no, transaction_id至少填一个
        appid, mchid, nonce_str不需要填入
        """
        url = "/pay/orderquery"

        return self._fetch(url, data)

    def close_order(self, out_trade_no, **data):
        """
        关闭订单
        out_trade_no必填
        appid, mchid, nonce_str不需要填入
        """
        url = "/pay/closeorder"

        data.setdefault("out_trace_no", out_trade_no)

        return self._fetch(url, data)

    def enterprise_payment(self, out_trade_no, open_id, amount=0, desc=''):
        '''
        使用企业对个人付款功能
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/tools/mch_pay.php?chapter=14_2

        api_cert_path: 微信支付商户证书路径，此证书(apiclient_cert.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        api_key_path: 微信支付商户证书路径，此证书(apiclient_key.pem)需要先到微信支付商户平台获取，下载后保存至服务器
        data: openid, check_name, re_user_name, amount, desc, spbill_create_ip
            openid: 用户openid
            check_name: 是否校验用户姓名
            re_user_name: 如果 check_name 为True，则填写，否则不带此参数
            amount: 金额: 企业付款金额，单位为分
            desc: 企业付款描述信息
            spbill_create_ip: 调用接口的机器Ip地址, 注：此地址为服务器地址
        :return: 企业转账结果
        '''
        url = self.weixinpay_domain + '/mmpaymkttransfers/promotion/transfers'
        data = {
            'mch_appid': self.app_id,
            'mchid': self.mch_id,
            'nonce_str': self.nonce_str,
            'partner_trade_no': out_trade_no,
            'openid': open_id,
            'check_name': 'NO_CHECK',
            'amount': amount,
            'desc': desc,
            'spbill_create_ip': '127.0.0.1'
        }
        data['sign'] = self.sign(data)

        # 证书
        dirname = os.path.dirname(os.path.abspath(__file__)) + '/cert/' + self.mch_id
        api_client_cert_path = dirname + '/apiclient_cert.pem'
        api_client_key_path = dirname + '/apiclient_key.pem'

        resp = self.sess.post(url, data=self.to_xml(data), cert=(api_client_cert_path, api_client_key_path))
        content = resp.content.decode("utf-8")

        if "return_code" in content:
            data = self.to_dict(content)
            if data['return_code'] == FAIL:
                logging.error(data['return_msg'])
            return data
        return content
