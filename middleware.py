import time
import logging
from django.http import Http404, HttpResponseServerError


class ResponseMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 需要授权的api接口会在header中传userid字段
        request.user_id = request.META.get("HTTP_USERID", "")
        request.app_id = request.META.get("HTTP_APPID", "")
        request.app_version = request.META.get("HTTP_APPVERSION", "")
        request.device_id = request.META.get("HTTP_DEVICEID", "")
        request.real_ip = request.META.get("HTTP_REAL_IP_FROM_API", "")
        # 语言
        request.lang = request.META.get('HTTP_LANG', 'zh')

        start_time = time.time()
        response = self.get_response(request)

        end_time = time.time()
        t = end_time - start_time
        if t >= 5:
            logging.error("LONG_PROCESS:%s%s %ss" % (request.get_host(), request.get_full_path(), int(t)))
        return response

    def process_exception(self, request, exception):
        from explorer_s_common import debug

        detail = "post_data is:" + str(request.POST) + debug.get_debug_detail(exception)
        detail += ("user_id:%s, app_id:%s, app_version:%s, device_id:%s" % (request.user_id, request.app_id, request.app_version, request.device_id))
        url = request.get_full_path()

        # 发送kafka消息
        from explorer_s_common.mq.mq_kafka import Producer, MQ_TOPIC_SYS_ERROR
        Producer().send(MQ_TOPIC_SYS_ERROR, {'service': url.split("/", 2)[1], 'url': url, 'detail': detail})
