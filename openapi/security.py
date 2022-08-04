import logging, json

from functools import wraps
from explorer_s_common.openapi.exception import OpenApiException
from explorer_s_common.openapi.sign import get_api
from explorer_s_common.utils import format_return
from explorer_s_common import inner_server
logger = logging.getLogger(__name__)


def open_api(version):
    """
    :param version:
    :return:
    """
    def fn(method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            openClass = get_api(version)
            request = args[0]
            code, msg = openClass.check_header(request)
            if code != 0:
                return format_return(code, msg=msg)
            # 获取密码
            app_id = request.headers.get("AppId")
            response = inner_server.get_app_info(app_id)
            if response.get('code', -1) != 0:
                return format_return(code=10002, msg='Invalid appid')
            result = response.get('data', {})
            if not result:
                return format_return(code=10002, msg='Invalid appid')
            app_secret = result.get('app_secret')
            if request.method == "GET":
                data = ""
            else:
                data = json.dumps(json.loads(request.body), separators=(',', ':'))
            if not openClass(request, app_id, app_secret).verify_sign(data):
                return format_return(code=20001, msg='Signature verification failed')
            try:
                return method(*args, **kwargs)
            except OpenApiException as e:
                return format_return(code=e.code, msg=e.msg)
            except AssertionError as e:
                return format_return(code=-1, msg=','.join(e.args))
            except Exception as e:
                logging.exception(str(e))
                return format_return(code=40000, msg='Unknown business error')
            finally:
               pass

        return wrapper

    return fn
