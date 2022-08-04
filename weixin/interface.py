import random
import string
import hashlib
import time
import requests
import json
import logging
import os
import base64
import datetime
from Crypto.Cipher import AES
from pyquery import PyQuery as pq

# 禁用安全请求警告
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from explorer_s_common import cache, consts, debug, inner_server
from explorer_s_common.weixin import config

weixin_api_url = 'https://api.weixin.qq.com'


class WeixinBase(object):

    def __init__(self, app_id=None, app_secret=None, origin_id=None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.origin_id = origin_id
        self.cache = cache.Cache()

    def __del__(self):
        del self.cache

    def get_formid_cache_key(self, user_id, formid_type=None):
        '''
        获取小程序formid的缓存key
        '''
        if formid_type:
            return "formids__%s__%s__%s" % (self.app_id, user_id, formid_type)
        else:
            return "formids__%s__%s" % (self.app_id, user_id)

    def get_weixin_access_token(self):
        key = 'wx_access_token_for_%s' % self.app_id
        access_token = self.cache.get(key)

        if access_token is None:
            # 正式服
            if os.getenv("DEVCODE", "dev") == 'prod':
                access_token, expires_in = self.get_weixin_access_token_directly()
                if access_token:
                    self.cache.set(key, access_token, int(expires_in))
        return access_token

    def get_weixin_access_token_directly(self):
        access_token, expires_in = '', 0
        content = ''
        url = '%s/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (
            weixin_api_url,
            self.app_id,
            self.app_secret
        )
        try:
            r = requests.get(url, timeout=10, verify=False)
            content = r.content
            r.raise_for_status()
            content = json.loads(content)
            access_token = content['access_token']
            expires_in = content['expires_in']
        except Exception as e:
            logging.error(u'get_weixin_access_token rep is %s' % content)
        return access_token, expires_in

    def get_weixin_jsapi_ticket(self):
        key = 'wx_jsapi_ticket_for_%s' % self.app_id
        ticket = self.cache.get(key)
        if ticket is None:
            ticket, expires_in = self.get_weixin_jsapi_ticket_directly()
            if ticket:
                self.cache.set(key, ticket, int(expires_in))
        return ticket

    def get_weixin_jsapi_ticket_directly(self):
        ticket, expires_in = '', 0
        content = ''

        url = '%s/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % (
            weixin_api_url, self.get_weixin_access_token()
        )
        try:
            r = requests.get(url, timeout=10, verify=False)
            content = r.content
            r.raise_for_status()
            content = json.loads(content)
            ticket = content['ticket']
            expires_in = content['expires_in']
        except Exception as e:
            logging.error(u'get_weixin_jsapi_ticket rep is %s' % content)
        return ticket, expires_in

    def get_user_info(self, openid):
        """
        @note: 获取一关注公众号的用户信息
        """
        access_token = self.get_weixin_access_token()
        url = '%s/cgi-bin/user/info?access_token=%s&openid=%s' % (weixin_api_url, access_token, openid)
        data = {}
        try:
            r = requests.get(url, timeout=10, verify=False)
            text = r.text
            r.raise_for_status()
            data = json.loads(text)
            if data.get("ermdsg") or data.get("subscribe") == 0:
                logging.error("error user info data is:%s" % data)
                data = {}
        except Exception as e:
            debug.get_debug_detail_and_send_email(e)
        return data

    def get_qr_code_ticket(self, expire=300, is_limit=False, scene_str=""):
        """
        @note: 获取二维码对应的ticket
        """
        access_token = self.get_weixin_access_token()
        url = '%s/cgi-bin/qrcode/create?access_token=%s' % (weixin_api_url, access_token)
        if not is_limit:
            data = '{"expire_seconds":%s, "action_name":"QR_STR_SCENE", "action_info": {"scene": {"scene_str": "%s"}}' % (expire, scene_str)
        else:
            data = '{"action_name":"QR_LIMIT_STR_SCENE", "action_info": {"scene": {"scene_str": "%s"}}' % scene_str
        data = data.encode('utf8')

        result = {}
        try:
            r = requests.post(url, data=data, timeout=10, verify=False)
            text = r.text
            r.raise_for_status()
            result = json.loads(text)
            if result.get("ermdsg") or result.get("subscribe") == 0:
                logging.error("error create_qr_code result is:%s" % result)
                result = {}
        except Exception as e:
            debug.get_debug_detail(e)
        return result

    def get_session_key(self, code):
        '''
        以code换取 用户唯一标识openid 和 会话密钥session_key
        '''
        openid = ''
        session_key = ''
        unionid = ''
        content = ''
        url = '%s/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % (
            weixin_api_url,
            self.app_id,
            self.app_secret,
            code
        )
        print(url)
        try:
            r = requests.get(url, timeout=10, verify=False)
            content = r.content
            r.raise_for_status()
            content = json.loads(content)
            openid = content['openid']
            session_key = content['session_key']
            unionid = content.get('unionid', None)

            # 保存到缓存
            key = 'wx_session_key_for_%s_%s' % (self.app_id, openid)
            self.cache.set(key, session_key, time_out=10 * 24 * 60 * 60)
        except Exception as e:
            logging.error(u'get_session_key rep is %s' % content)
        return openid, session_key, unionid

    def get_session_key_from_cache(self, open_id):
        '''
        从缓存中获取session_key
        '''
        key = 'wx_session_key_for_%s_%s' % (self.app_id, open_id)
        session_key = self.cache.get(key)
        return session_key

    def decrypt_data(self, open_id, encrypted_data, iv):
        '''
        解密数据
        '''
        session_key = self.get_session_key_from_cache(open_id)
        if session_key:
            return WXBizDataCrypt(self.app_id, session_key).decrypt(encrypted_data, iv)
        else:
            return {}

    def save_form_id(self, user_id, form_id, formid_type=None):
        '''
        保存form_id
        '''
        cache_key = self.get_formid_cache_key(user_id, formid_type)
        days = 7 * 24 * 60 * 60
        cache_max_length = 20

        cache_obj = cache.Cache(cache.CACHE_WEIXIN)
        form_ids = cache_obj.get(cache_key) or {}

        # 数据格式为 {"timestamp": "form_id"}
        timestamp = datetime.datetime.now().timestamp() + days
        # 微信支付可以发3次
        if formid_type == "pay":
            form_ids[timestamp] = {'form_id': form_id, 'count': 3}
        else:
            form_ids[timestamp] = {'form_id': form_id, 'count': 1}

        # 排序 只保留20位长度
        keys = list(form_ids.keys())
        keys.sort()

        # 如果超过最大长度
        if len(keys) > cache_max_length:
            delete_keys = keys[:len(keys) - cache_max_length]
            for key in delete_keys:
                form_ids.pop(key)

        cache_obj.set(cache_key, form_ids, time_out=days)

    def get_form_id(self, user_id, formid_type=None):
        '''
        获取form_id
        '''
        cache_key = self.get_formid_cache_key(user_id, formid_type)

        cache_obj = cache.Cache(cache.CACHE_WEIXIN)
        form_ids = cache_obj.get(cache_key) or {}

        today = datetime.datetime.now().timestamp()
        active_key = None
        active_form_id = None
        active_count = 1
        # 从时间最小的开始取
        keys = list(form_ids.keys())
        keys.sort()

        for key in keys:
            # 判断是否已经过期
            if key <= today:
                form_ids.pop(key)
            else:
                active_key = key
                active_form_id = form_ids[active_key]
                # 兼容处理
                if isinstance(active_form_id, dict):
                    active_count = active_form_id['count']
                    active_form_id = active_form_id['form_id']
                break

        if active_form_id:
            active_count -= 1

            # 使用之后删除此form_id
            if active_count <= 0:
                form_ids.pop(active_key)
            else:
                form_ids[active_key]['count'] = active_count

            # 重新写入缓存
            timeout = cache_obj.ttl(cache_key)
            timeout = 7 * 24 * 60 * 60 if timeout < 0 else timeout
            cache_obj.set(cache_key, form_ids, time_out=timeout)

        return active_form_id

    def send_wxapp_template_msg(self, open_id, template_id, page, form_id, data, emphasis_keyword=""):
        '''
        发送小程序模板消息
        '''
        access_token = self.get_weixin_access_token()
        url = '%s/cgi-bin/message/wxopen/template/uniform_send?access_token=%s' % (weixin_api_url, access_token)

        post_data = {
            "touser": open_id,
            "weapp_template_msg": {
                "template_id": template_id,
                "page": page,
                "form_id": form_id,
                "data": data,
                "emphasis_keyword": emphasis_keyword
            }
        }

        errcode, ermdsg = 0, consts.ERROR_DICT.get(0)
        try:
            r = requests.post(url, data=json.dumps(post_data), timeout=10, verify=False)
            text = r.text
            r.raise_for_status()
            result = json.loads(text)
            return result["errcode"], result["ermdsg"]
        except Exception as e:
            debug.get_debug_detail(e)
            return 99904, consts.ERROR_DICT.get(99904)

    def send_mp_template_msg(self, open_id, template_id, page, data, mp_app_id, template_jump_url):
        '''
        发送公众号模板消息
        '''
        access_token = self.get_weixin_access_token()
        url = '%s/cgi-bin/message/wxopen/template/uniform_send?access_token=%s' % (weixin_api_url, access_token)

        post_data = {
            "touser": open_id,
            "mp_template_msg": {
                "appid": mp_app_id,
                "template_id": template_id,
                "url": template_jump_url,
                "miniprogram": {
                    "appid": self.app_id,
                    "path": page
                },
                "data": data
            }
        }

        errcode, ermdsg = 0, consts.ERROR_DICT.get(0)
        try:
            r = requests.post(url, data=json.dumps(post_data), timeout=10, verify=False)
            text = r.text
            r.raise_for_status()
            result = json.loads(text)
            return result["errcode"], result["ermdsg"]
        except Exception as e:
            debug.get_debug_detail(e)
            return 99904, consts.ERROR_DICT.get(99904)

    def get_customer_service_response(self, to_user, from_user):
        return u'''
        <xml>
        <ToUserName><![CDATA[%(to_user)s]]></ToUserName>
        <FromUserName><![CDATA[%(from_user)s]]></FromUserName>
        <CreateTime>%(timestamp)s</CreateTime>
        <MsgType><![CDATA[transfer_customer_service]]></MsgType>
        </xml>
        ''' % dict(to_user=from_user, from_user=to_user, timestamp=int(time.time()))

    def format_input_xml(self, xml):
        '''
        @note: 标签替换为小写，以便pyquery能识别
        '''
        for key in ['ToUserName>', 'FromUserName>', 'CreateTime>', 'MsgType>', 'Content>', 'MsgId>', 'PicUrl>',
                    'MediaId>', 'Format>', 'ThumbMediaId>', 'Event>', 'EventKey>', 'Ticket>', 'Recognition>',
                    'DeviceID>', 'SessionID>', 'DeviceType>', 'OpenID>']:
            xml = xml.replace(key, key.lower())
        return xml

    def get_response(self, xml):

        xml = self.format_input_xml(xml)
        jq = pq(xml)
        to_user = jq('tousername')[0].text
        from_user = jq('fromusername')[0].text
        events = jq('event')
        app_key = self.get_app_key_by_origin_id(to_user)
        logging.error(u'收到一个来自app：%s 的请求' % app_key)

        # if "test" in app_key:   # 剔除测试公众号发送信息
        #     return

        # 事件
        if events:
            event = events[0].text.lower()
            event_key = ""
            event_keys = jq('eventkey')
            if event_keys:
                event_key = event_keys[0].text

            event_key = event_key.replace("qrscene_", "")

            # 扫码事件
            if event in ('scan', 'subscribe'):
                event_key = event_key or 'subscribe'

            # 关注事件
            if event in ('subscribe',):
                content = u'''Hey，你终于来啦！

我们的目标是吃得健康，活得漂亮！解决肥胖、高血压和高血糖！

查查食物中的碳水化合物：
<a href=https://www.codoonhealth.com/ data-miniprogram-appid=wxfbe8c098f4787741 data-miniprogram-path=pages/index/index>哪些是健康的低碳水食物?</a>

一个小测试：
<a href=https://www.codoonhealth.com/ data-miniprogram-appid=wxad8fd8b0383b4470 data-miniprogram-path=pages/health?redirect_url=/package_tool/pages/ideal_model>测测你的身材是否达到理想状态</a>
'''
                self.send_msg_to_weixin(content, from_user, msg_type='text')

                temp = {
                    "type": "news",
                    "title": "精选健康知识",
                    "description": "瘦身方法、减肥指南、健康饮食",
                    "url": "https://mp.weixin.qq.com/mp/homepage?__biz=MzIyMTk3MDY3OA==&hid=24&sn=014824bb4abfb78d5d5611c48f4e5403",
                    "picurl": "https://mmbiz.qpic.cn/mmbiz_png/uZNdD4omXOm0cxRzrXnRWricXNI2kxNS25AkMCOTvtXwAm713MKIp2GUsZVh6LJib0ibwOD0KzvMC8sUUrwegjhyQ/0?wx_fmt=png"
                }
                img_info = u'[{"title": "%s", "description": "%s", "url": "%s", "picurl": "%s"}]' \
                    % (temp['title'], temp['description'], temp['url'], temp['picurl'])
                self.send_msg_to_weixin("", from_user, msg_type=temp['type'], img_info=img_info)

            elif event in ('click', ):
                event_key = jq('eventkey')[0].text.lower()
                if event_key == 'company':
                    temp = {
                        "type": "news",
                        "title": "选择咕咚健康企业服务，为员工健康保驾护航。",
                        "description": "",
                        "url": "https://mp.weixin.qq.com/s?__biz=MzIyMTk3MDY3OA==&mid=100002293&idx=1&sn=34630f32724153c73f5ff1bf574012d5&scene=19#wechat_redirect",
                        "picurl": "https://mmbiz.qpic.cn/mmbiz_png/uZNdD4omXOkYqNaQ4siaoF1yNCwHKXTz0dCccKDLErpnIYvGcOHZkbic0Yz1ic1ZGvn8pyAYK8tq9SIywH06ZmdkA/0?wx_fmt=png"
                    }
                    img_info = u'[{"title": "%s", "description": "%s", "url": "%s", "picurl": "%s"}]' \
                        % (temp['title'], temp['description'], temp['url'], temp['picurl'])
                    self.send_msg_to_weixin("", from_user, msg_type=temp['type'], img_info=img_info)

            elif event in ('unsubscribe'):
                # 发送kafka消息处理
                from ch_common.mq.mq_kafka import Producer, MQ_TOPIC_UN_SUB
                Producer().send(MQ_TOPIC_UN_SUB, {'open_id': from_user})

        # 文字识别
        msg_types = jq('msgtype')
        if msg_types:
            msg_type = msg_types[0].text
            if msg_type == 'text':
                content = jq('content')[0].text.strip()
                logging.error(u'收到用户发送的文本数据，内容如下：%s' % content)

                # 查询回复
                replies = inner_server.get_weixin_keyword_replay(word=content)

                # 循环处理
                for temp in replies:
                    if temp['type'] == "news":
                        img_info = u'[{"title": "%s", "description": "%s", "url": "%s", "picurl": "%s"}]' \
                            % (temp['title'], temp['description'], temp['url'], temp['picurl'])
                        self.send_msg_to_weixin(content, from_user, msg_type=temp['type'], img_info=img_info)
                    if temp['type'] == "image":
                        self.send_msg_to_weixin('', from_user, msg_type=temp['type'], img_info=temp['media_id'])
                    if temp['type'] == "mpnews":
                        self.send_msg_to_weixin('', from_user, msg_type=temp['type'], img_info=temp['media_id'])
                    if temp['type'] == "text":
                        self.send_msg_to_weixin(temp['content'], app_key, msg_type=temp['type'], img_info="")

                return self.get_customer_service_response(to_user, from_user)   # 多客服接管

    def get_app_key_by_origin_id(self, origin_id):
        # todo...
        for key in config.DICT_WEIXIN_APP:
            if config.DICT_WEIXIN_APP[key]['origin_id'] == origin_id:
                return key
        raise Exception('app_key not found by: %s' % origin_id)

    def send_msg_to_weixin(self, content, to_user, msg_type='text', img_info=''):
        '''
        @note: 发送信息给微信
        '''
        # json的dumps字符串中中文微信不识别，修改为直接构造
        if msg_type == 'text':
            data = u'{"text": {"content": "%s"}, "msgtype": "%s", "touser": "%s"}' % (content, msg_type, to_user)
        elif msg_type == 'image':
            data = u'{"image":{"media_id": "%s"}, "msgtype":"%s", "touser": "%s"}' % (img_info, msg_type, to_user)
        elif msg_type == 'mpnews':
            data = u'{"mpnews":{"media_id": "%s"}, "msgtype":"%s", "touser": "%s"}' % (img_info, msg_type, to_user)
        else:
            data = u'{"news":{"articles": %s}, "msgtype":"%s", "touser": "%s"}' % (img_info, msg_type, to_user)

        data = data.encode('utf8')

        access_token = self.get_weixin_access_token()
        url = '%s/cgi-bin/message/custom/send?access_token=%s' % (weixin_api_url, access_token)

        for i in range(3):
            try:
                r = requests.post(url, data=data, timeout=5, verify=False)
                break
            except:
                pass

        r.raise_for_status()
        content = json.loads(r.content)
        logging.error('send msg to weixin resp is %s' % (content,))


class Sign(object):

    def __init__(self, app_id, jsapi_ticket, url):
        self.app_id = app_id
        self.ret = {
            'nonceStr': self.__create_nonce_str(),
            'jsapi_ticket': jsapi_ticket,
            'timestamp': self.__create_timestamp(),
            'url': url
        }

    def __create_nonce_str(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def __create_timestamp(self):
        return int(time.time())

    def sign(self):
        string = '&'.join(['%s=%s' % (key.lower(), self.ret[key]) for key in sorted(self.ret)])
        self.ret['signature'] = hashlib.sha1(string.encode('utf-8')).hexdigest()
        self.ret['app_id'] = self.app_id
        return self.ret


class WXBizDataCrypt(object):
    '''
    小程序解密类

    WXBizDataCrypt(app_key, session_key).decrypt(encryptedData, iv)
    '''

    def __init__(self, app_id, session_key):
        self.app_id = app_id
        self.session_key = session_key

    def decrypt(self, encryptedData, iv):
        # base64 decode
        session_key = base64.b64decode(self.session_key)
        encryptedData = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)

        cipher = AES.new(session_key, AES.MODE_CBC, iv)

        decrypted = json.loads(self._unpad(cipher.decrypt(encryptedData)))

        if decrypted['watermark']['appid'] != self.app_id:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]
