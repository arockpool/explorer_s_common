import json
import hmac
import hashlib
import datetime
import uuid
from explorer_s_common.cache import Cache
from requests import request as do_request

ALLOWED_VERSIONS = ['V1']


class OpenApi:
    def __init__(self, request, appkey, appsecret, host=None, authorization=None):
        self.request = request
        self.host = host
        self.appkey = appkey
        self.appsecret = appsecret
        self.authorization = authorization
        self._headers = None

    def __call__(self, appkey, appsecret):
        self.appkey = appkey
        self.appsecret = appsecret

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        self._headers = headers

    def build_sign_sha256(self, sign_str, appsecret):
        """
        使用HMAC-SHA256签名
        :param sign_str:
        :param appsecret:
        :return:
        """
        s = hmac.new(appsecret.encode(), sign_str.encode(), digestmod=hashlib.sha256)
        signature = s.hexdigest()
        return signature

    def verify_sign_sha256(self, sign_str, verify_str, appsecret):
        """
        验证签名
        :param sign_str: 被签名的数据
        :param verify_str: 签名的结果
        :param appsecret:
        :return:
        """
        s = hmac.new(appsecret.encode(), sign_str.encode(), digestmod=hashlib.sha256)
        signature = s.hexdigest()
        if verify_str == signature:
            return True
        else:
            return False

    def verify_sign(self, data):
        """
        V1版本验证签名
        :param headers: Request header
        :param data: Request Data
        :param appsecret:
        :return:
        """
        sign_str = self.structure_data(data, self.request.headers.get('Timestamp'), self.request.headers.get('SignatureNonce'))
        result = self.verify_sign_sha256(sign_str, self.request.headers.get('Signature'), self.appsecret)
        return result

    def sign(self, headers, data):
        """
        V1生产验证签名
        :param headers:
        :param data: Request Data
        :param appsecret:
        :return:
        """
        sign_str = self.structure_data(data, headers.get('Timestamp'), headers.get('SignatureNonce'))
        return self.build_sign_sha256(sign_str, self.appsecret)

    def build_headers(self, method, url, data=None):
        """
        构建回调 headers
        :param appsecret:
        :param body:
        :return:
        """
        headers = {
            'AppId': self.appkey,
            'Authorization': self.authorization,
            'Timestamp': datetime.datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z'),
            'SignatureVersion': 'V1',
            'SignatureMethod': 'HMAC-SHA256',
            'SignatureNonce': uuid.uuid4().hex,
            'Signature': '',
        }

        if method.lower() in ['get', 'delete']:
            payload = ''
        if method.lower() in ['post', 'put']:
            payload = json.dumps(data or {}, separators=(',', ':'))

        sing = self.sign(headers, payload)
        headers['Signature'] = sing
        self.headers = headers
        return headers

    def send(self, method, uri, data=None):
        headers = self.build_headers(method, uri, data)
        response = do_request(method=method, url=self.host + uri, params=data, headers=headers)
        return response.status_code, response.json()

    @classmethod
    def check_header(cls, request):
        headers = request.headers
        arg_list = ['AppId', 'Timestamp', 'SignatureVersion', 'SignatureMethod', 'SignatureNonce', 'Signature']
        for arg in arg_list:
            if not headers.get(arg):
                return 10400, 'headers validation failed, missing parameter:{0}'.format(arg)
        if headers.get('SignatureVersion') not in ALLOWED_VERSIONS:
            return 10001, 'Unsupported version of the interfac'
        # YYYY-MM-DDThh:mm:ssZ，T表示间隔，Z代表0时区
        timestamp = datetime.datetime.strptime(headers.get('Timestamp'), '%Y-%m-%dT%H:%M:%S%z')
        utcnow = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).astimezone(timestamp.tzinfo)
        if utcnow > timestamp + datetime.timedelta(seconds=60):
            return 10403, 'The request was rejected, timed out'
        nonce = headers.get('SignatureNonce')
        if Cache().exists(nonce):
            return 10403, 'The request was rejected, SignatureNonce already exists'
        else:
            Cache().set(nonce, "", 3600 * 24 * 5, original=True)
        return 0, ''


class V1(OpenApi):
    def structure_data(self, json_str, timestamp, sign_nonce):
        """
        V1构建加密数据
        :param json_str:
        :param timestamp: 时间搓
        :param sign_nonce: 签名随机数
        :return:
        """
        sign_str = 'body={0}&timestamp={1}&signatureNonce={2}'.format(json_str, timestamp, sign_nonce)
        return sign_str


def get_api(version):
    if version == 'V1':
        return V1

    assert False, 'Unsupported version of the interface'
