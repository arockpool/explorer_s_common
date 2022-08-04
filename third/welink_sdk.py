import os
import time
import requests
import logging
import hashlib
from random import Random

from explorer_s_common import debug, utils


class WeLinkBase(object):

    def __init__(self, init_dict={}):
        if init_dict.get('api_domain'):
            self.api_domain = init_dict.get('api_domain')
            self.account_id = init_dict.get('account_id')
            self.SMmsEncryptKey = init_dict.get('sms_encrypt_key')
            self.Password = init_dict.get('password')
            self.timeout = 10
            self.product_id = init_dict.get("product_id")
        else:
            self.api_domain = os.getenv("WELINK_API_DOMIAN", "https://api.51welink.com")
            self.account_id = os.getenv("WELINK_ACCOUNTID", "YDNKC_001")
            self.SMmsEncryptKey = os.getenv("WELINK_SMMSENCRYPTKEY", "SMmsEncryptKey")
            self.Password = os.getenv("WELINK_PASSWORD", "ydnyc20201")
            self.product_id = init_dict.get("product_id")
            self.timeout = 10

    def sign(self, data: dict):
        access_data = "AccountId=%s&PhoneNos=%s&Password=%s&Random=%d&Timestamp=%s" % (
            self.account_id,
            data.get("PhoneNos"),
            str(hashlib.md5((self.Password + self.SMmsEncryptKey).encode("utf-8")).hexdigest()).upper(),
            data.get("Random"),
            data.get("Timestamp")
        )
        access_key = hashlib.sha256(access_data.encode("utf-8")).hexdigest()
        data.update({"AccessKey": access_key})

        return data

    def request_api(self, uri, data: dict):
        try:
            headers = {
                'Accept': 'application/json;charset=utf-8',
                'Content-Type': "application/x-www-form-urlencoded"
            }

            r = requests.post(self.api_domain + uri, data=self.sign(data), timeout=self.timeout, headers=headers)
            r.raise_for_status()
            result = r.json()
            logging.info(result)
            print(result)

            if result.get("Result") != "succ":
                logging.error(result.get("Reason"))
            data.update({"back_msg": result.get("Reason")})
            return utils.format_return(0, data=data)
        except Exception as e:
            logging.error(e)
            return utils.format_return(99904, msg="短信网关请求失败")

    def send_sms(self, phone_no, content, is_hard=False, product_id="1012818"):
        """
        :param phone_no:
        :param content:
        :param is_hard: 是否重催
        :return: bool
        """
        # product_id = "1012808"  # 行业短信
        if is_hard:
            product_id = "1012812"
        if "验证码" in content:  # 验证码
            product_id = self.product_id
        uri = "/EncryptionSubmit/SendSms.ashx"
        data = {
            "AccountId": self.account_id,
            "Timestamp": str(int(time.time())),
            "Random": Random().randint(1, 9223372036854775807),
            "ExtendNo": "",
            "ProductId": product_id,
            "PhoneNos": phone_no,
            "Content": content
        }

        return self.request_api(uri=uri, data=data)


if __name__ == '__main__':
    # sms = WeLinkBase()
    # # qs.send_sms("15208411129", 40747, [1818, ])
    # # qs.send_voice("15208411129", "1818")
    # result = sms.send_sms("18728408084", "验证码123456，欢迎注册/登录FILSWAP，请勿泄露短信验证码。【海链数字】")

    # sms = WeLinkBase(init_dict={
    #     "api_domain": "https://api.51welink.com",
    #     "account_id": "YDNKC_001",
    #     "sms_encrypt_key": "SMmsEncryptKey",
    #     "password": "ydnyc20201",
    #     "product_id": "1012809"
    # })
    # result = sms.send_sms("0014752211134", "验证码123456，测试使用，请勿泄露短信验证码。【海链数字】")
    # print(result)

    sms = WeLinkBase(init_dict={
        "api_domain": "https://api.51welink.com",
        "account_id": "YDNKC_001",
        "sms_encrypt_key": "SMmsEncryptKey",
        "password": "ydnyc20201",
        "product_id": "1012818"
    })
    result = sms.send_sms("18728408084", "	验证码883586，您正在进行登录操作，请勿泄露短信验证码。【一石云池】")
    print(result)
