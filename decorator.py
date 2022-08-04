import json
import datetime

from functools import wraps
from django.http import HttpResponse, JsonResponse
from explorer_s_common import cache, debug
from explorer_s_common.utils import format_return


def common_ajax_response(func):
    """
    @note: 通用的ajax返回值格式化，格式为：dict(code=0, msg='', data={})
    """
    def _decorator(request, *args, **kwargs):
        result = func(request, *args, **kwargs)
        if isinstance(result, HttpResponse):
            return result
        code, msg, data = result

        r = dict(code=code, msg=msg, data=data)
        response = JsonResponse(r)
        # response['Access-Control-Allow-Origin'] = '*'

        return response
    return _decorator


def validate_params(func):
    """
    @note: 通用的参数校验，第一步非空校验
    """
    def _decorator(*args, **kwargs):

        def _get_param_items(func, args, kwargs):
            import inspect
            parameters = inspect.signature(func).parameters
            arg_keys = tuple(parameters.keys())
            vparams = [k for k, v in parameters.items() if k == str(v)]

            param_items = []
            # collect args   *args 传入的参数以及对应的函数参数注解
            for i, value in enumerate(args):
                _key = arg_keys[i]
                if _key in vparams:
                    param_items.append([_key, value])

            # collect kwargs  **kwargs 传入的参数以及对应的函数参数注解
            for arg_name, value in kwargs.items():
                if arg_name in vparams:
                    param_items.append([arg_name, value])

            return param_items

        check_list = _get_param_items(func, args, kwargs)
        # 不能为空检测
        for item in check_list:
            if item[1] is None:
                return format_return(99901)

        return func(*args, **kwargs)

    return _decorator


def cache_required(cache_key, cache_key_type=0, expire=3600 * 24, cache_config=cache.CACHE_TMP):
    '''
    @note: 缓存装饰器
    cache_key格式为举例：1：'answer_summary_%s' 取方法的第一个参数值做键 2：'global_var'固定值作键
    如果cache_key有%需要格式化的话，通过cache_key_type来控制：
    0：传参为：func(self, cache_key_param)，取cache_key_param或者cache_key_param.id
    1：传参为：func(cache_key_param)
    2：传参为：func(self) cache_key为self.id
    '''

    def _wrap_decorator(func):

        func.cache_key = cache_key

        def _decorator(*args, **kwargs):
            cache_key = func.cache_key
            must_update_cache = kwargs.get('must_update_cache')

            if '%' in cache_key:
                assert len(args) > 0
                if cache_key_type == 0:
                    key = args[1].id if hasattr(args[1], 'id') else args[1]
                    if isinstance(key, (str, int, float)):
                        cache_key = cache_key % key
                    else:
                        return
                if cache_key_type == 1:
                    cache_key = cache_key % args[0]
                if cache_key_type == 2:
                    cache_key = cache_key % args[0].id
            return cache.get_or_update_data_from_cache(cache_key, expire, cache_config,
                                                       must_update_cache, func, *args, **kwargs)
        return _decorator
    return _wrap_decorator


def one_by_one_locked(func):
    """
    @note: 线程锁，避免并发问题，比如python的get_or_create问题
    限定了参数传输的方式，(self, user_id)或者只有self参数
    """
    def _decorator(*args, **kwargs):
        import time
        import uuid

        cache_obj = cache.Cache()

        # 缓存取第一个arg或者第一个kwargs
        cache_key_suffix = ""
        if len(args) > 1:
            cache_key_suffix = args[1]
        else:
            if kwargs:
                cache_key_suffix = list(kwargs.items())[0][1]

        cache_key = "%s_%s" % (func.__name__, cache_key_suffix)  # 缓存的键目前只支持特定规则

        uuid_str = str(uuid.uuid4())
        flag = None

        while not flag:
            flag = cache_obj.set_lock(cache_key, uuid_str, ex=5, nx=True)  # 加锁
            if not flag:
                time.sleep(0.1)

        r = func(*args, **kwargs)
        if cache_obj.get(cache_key) == uuid_str:
            cache_obj.delete(cache_key)  # 处理完成后删除锁
        return r

    return _decorator


def login_required(permission):
    '''
    登录验证装饰器

    @login_required()
    def delete(request):
        pass

    '''
    def login_decorator(func):

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.user_id:
                return func(request, *args, **kwargs)
            else:
                return format_return(99905)
        return wrapper
    return login_decorator


def lang_translate(func):
    '''
    语言装饰器

    @lang_translate
    def delete(request):
        pass

    '''
    @wraps(func)
    def wrapper(request, *args, **kwargs):

        result = list(func(request, *args, **kwargs))
        if request.lang != 'zh':
            from explorer_s_common.consts import ERROR_DICT
            result[1] = ERROR_DICT.get(request.lang).get(result[0], result[1])
        return result

    return wrapper


def convert_user_id(func):
    '''
    转换user_id

    @convert_user_id
    def something(request):
        pass

    '''
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user_id:
            from explorer_s_common import inner_server
            external_user_id = request.POST.get('external_user_id')
            source = request.POST.get('source', request.app_id)
            result = inner_server.get_user_info_by_thirdapp(external_user_id=external_user_id, source=source)
            request.user_id = result.get('data', {}).get('user_id')
        return func(request, *args, **kwargs)
    return wrapper


def add_request_log(assign_appids=[]):
    """
    记录日志方式,将消息写入
    :param func:
    :return:
    """
    def wrapper(func):

        @wraps(func)
        def _decorator(*args, **kwargs):
            from django.core.handlers.wsgi import WSGIRequest
            start_time = datetime.datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.datetime.now()

            # views处理
            if args and isinstance(args[0], WSGIRequest):
                request = args[0]
                url = request.get_full_path()
                post_data = '%s \n===========================================\n %s' % (request.META, request.POST)
                res_data = json.dumps(result, ensure_ascii=False)
                request_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                duration = (end_time - start_time).total_seconds()
                app_id = request.app_id
                ip = request.real_ip
            else:
                url = func.__name__
                post_data = 'args: %s, kwargs: %s' % (args or [], kwargs or {})
                res_data = json.dumps(result, ensure_ascii=False)
                request_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                duration = (end_time - start_time).total_seconds()
                app_id = None
                ip = None

            flag = True
            # 如果指定了app_id
            if assign_appids and app_id not in assign_appids:
                flag = False
            if flag:
                # 发送kafka消息
                from explorer_s_common.mq.mq_kafka import Producer, MQ_TOPIC_REQUEST_LOG
                Producer().send(MQ_TOPIC_REQUEST_LOG, {
                    'url': url, 'post_data': post_data, 'res_data': res_data, 'ip': ip,
                    'request_time': request_time, 'duration': duration, 'app_id': app_id
                })
            return result
        return _decorator

    return wrapper
