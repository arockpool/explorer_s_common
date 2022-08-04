import re
import json
import time
import random
import datetime
import decimal

from django.core.validators import BaseValidator
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from explorer_s_common.consts import ERROR_DICT
from explorer_s_common import debug
from explorer_s_common.cache import Cache


def get_order_no(prefix=""):
    '''
    生成订单号
    '''
    return '%s%s%03d' % (prefix, datetime.datetime.now().strftime(
        '%Y%m%d%H%M%S%f')[:-3], random.randint(0, 999))


def format_return(code, msg='', data=None, change_none=False):
    '''
    格式化返回值
    '''
    temp = data if data is not None else {}

    # 是否要将None变成""
    if change_none:
        temp = json.loads(json.dumps(temp).replace('null', '""'))
    return code, msg or ERROR_DICT.get(code, ''), temp


def format_number(number):
    '''
    格式化数字
    '''
    return number.quantize(decimal.Decimal('0.00')) if number is not None else ""


def format_date_time(datetime):
    '''
    格式时间
    '''
    return datetime.strftime('%Y-%m-%d %H:%M:%S') if datetime else ""


def format_date(datetime):
    '''
    格式时间
    '''
    return datetime.strftime('%Y-%m-%d') if datetime else ""


def get_ip(request):
    # 获取客户端ip
    if 'HTTP_REAL_IP_FROM_API' in request.META:
        return request.META['HTTP_REAL_IP_FROM_API']
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        client_ip = request.META['HTTP_X_FORWARDED_FOR']
        arr_ip = client_ip.split(',', 1)
        return arr_ip[0].strip()
    elif 'HTTP_X_REAL_IP' in request.META:
        return request.META['HTTP_X_REAL_IP']
    else:
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


def generate_date_range(start_date_str, end_date_str):
    '''
    生成日期区间
    '''
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
    dates = [start_date_str]
    count = 0

    # 限制最大生成不超过1000的区间
    while count < 1000:

        # 如果开始日期和结束日期相同则直接跳出
        if start_date_str == end_date_str:
            break

        count += 1
        temp = (
                start_date +
                datetime.timedelta(
                    days=count)).strftime('%Y-%m-%d')
        dates.append(temp)
        if temp == end_date_str:
            break
    return dates


def format_datetime(value, suffix="minute", get_short=True):
    if not value:
        return 'datetime error'
    d = value
    if not isinstance(value, datetime.datetime):
        d = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    now_date = datetime.datetime.now()
    ds = time.time() - time.mktime(d.timetuple())  # 秒数
    # dd = now_date - d  # 日期相减对象
    if ds <= 5:
        return u'刚刚'
    if ds < 60:
        return '%d秒前' % ds
    if ds < 3600:
        return '%d分钟前' % (ds / 60,)

    suffix_format = '%H:%M:%S'
    if suffix == "second":
        suffix_format = '%H:%M:%S'
    if suffix == "minute":
        suffix_format = '%H:%M'

    d_change = now_date.day - d.day
    if ds < 3600 * 24 * 3:
        if d_change == 0:
            return '今天%s' % d.strftime(suffix_format)
        if d_change == 1:
            return '昨天%s' % d.strftime(suffix_format)
        if d_change == 2:
            return '前天%s' % d.strftime(suffix_format)
    y_change = now_date.year - d.year
    suffix_format = "" if get_short else (" " + suffix_format)
    if y_change == 0:
        return '%s' % d.strftime('%m-%d' + suffix_format)
    if y_change == 1:
        return '去年%s' % d.strftime('%m月%d日' + suffix_format)
    if y_change == 2:
        return '前年%s' % d.strftime('%m月%d日' + suffix_format)
    return '%s年前%s' % (y_change, d.strftime('%m月%d日'))


def format_price(price, point=2, round_flag=decimal.ROUND_HALF_EVEN):
    '''
    格式化价格
    round_flag:小数保留标志
    '''
    return str(decimal.Decimal(price).quantize(decimal.Decimal("1.{}".format('0' * point)),
                                               round_flag) if price is not None else '')
    # return ('%.' + str(point) + 'f') % decimal.Decimal(price).quantize(decimal.Decimal()) if price is not None else ''


def format_fil(num, point=4, round_flag=decimal.ROUND_HALF_EVEN):
    '''
    格式化价格
    '''
    num = decimal.Decimal(num) / 10 ** 18
    return format_price(price=num, point=point, round_flag=round_flag)


def format_fil_to_decimal(num, round_data=None):
    '''
    格式化价格
    '''

    num = decimal.Decimal(num) / 10 ** 18
    if round_data:
        return round(num, round_data)
    return num


def format_fil_to_decimal_verification(num):
    '''
    格式化,需要进行验证操作
    仅转换乘过10^18的数据
    '''
    try:
        num = decimal.Decimal(num)
    except:
        return num
    else:
        if num > 10 ** 10 or num < -10 ** 10:
            num = num / 10 ** 18
        else:
            return num
    finally:
        return num


def un_format_fil_to_decimal(num, point=4):
    '''
    反格式化价格,乘10^18
    '''
    num = decimal.Decimal(num) * 1000000000000000000
    return num


def format_result_dict(result_dict):
    """
    将参数进行格式化操作(除10^18)
    """
    return dict(zip(result_dict, map(format_fil_to_decimal_verification, result_dict.values())))


def format_result_dict_auto_unit(result_dict):
    """
    将参数进行格式化操作(除10^18)
    """
    return dict(zip(result_dict, map(format_coin_to_str, result_dict.values())))


def clear_html_tag(text):
    '''
    去除掉所有的html标签
    '''
    from html.parser import HTMLParser
    html_parser = HTMLParser()
    temp_text = html_parser.unescape(text)

    rule = re.compile(r'<[^>]+>', re.S)
    return rule.sub('', temp_text) if text else text


def generate_random_num(length=4):
    '''
    随机号码
    '''
    return ''.join([random.choice('123456789ABCDEFGHJKLMNPQRSTUVWXYZ')
                    for x in range(length)])


def generate_tx_code():
    return datetime.datetime.now().replace(microsecond=0).strftime(
        "%Y%m%d%H%M%S") + (generate_random_num(length=18))


def format_power(power, unit='DiB'):
    '''
    格式化power
    '''
    units = ["Bytes", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB", "BiB", "NiB", "DiB"]
    unit_index = 0

    power = decimal.Decimal(power)
    _power = abs(power)
    temp = _power
    while (temp >= 1024) and (unit_index <= len(units)):
        unit_index += 1
        temp = temp / 1024
        if units[unit_index] == unit:
            break

    # 正负判断
    return '%s%s %s' % ('-' if power < 0 else '', format_price(temp), units[unit_index])


def format_power_to_TiB(power):
    '''
    格式化power
    '''
    units = ["Bytes", "KiB", "MiB", "GiB", "TiB"]
    unit_index = 0

    power = decimal.Decimal(power)
    temp = power
    while (abs(temp) > 1024) and (unit_index < len(units) - 1):
        unit_index += 1
        temp = temp / 1024

    return '%s %s' % (format_price(temp), units[unit_index])


def str_2_power(power_str):
    '''
    根据算力字符串还原成byte
    '''
    if power_str == "" or power_str is None:
        return power_str
    mapping = {
        'NiB': 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
        'YiB': 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
        'ZiB': 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
        'EiB': 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
        'PiB': 1024 * 1024 * 1024 * 1024 * 1024,
        'TiB': 1024 * 1024 * 1024 * 1024,
        'GiB': 1024 * 1024 * 1024,
        'MiB': 1024 * 1024,
        'KiB': 1024,
        'Bytes': 1
    }

    value, unit = power_str.split(' ')
    return int(float(value) * mapping.get(unit, 1))


def get_aggregate_gas(sector_numbers, base_fee, height=1231620, msg_method=26):

    """
    ProveCommitAggregate除了按之前方法取gas外，还需要按下述描述，计算聚合费用
    lotus v1.10.0仅对ProveCommitAggregate收取消息聚合费
    lotus v1.12.0对PreCommitSectorBatch和ProveCommitAggregate都收取聚合费
    """
    if msg_method not in [25, 26]:
        return 0
    batch_discount = 1 / 20  # unitless批量证明折扣，固定
    if height >= 1231620:
        batch_balancer = 5 * (10 ** 9)  # attoFIL 批量证明最低限额，固定
        if msg_method == 25:
            single_proof_gas_usage = 16433324.1825  # SinglePreCommitGasUsage = 16433324.1825   单扇区证明gas费率，固定
        if msg_method == 26:
            single_proof_gas_usage = 49299972.5475  # SingleProveCommitGasUsage = 49299972.5475 单扇区证明gas费率，固定
    else:
        batch_balancer = 2 * (10 ** 9)  # attoFIL 批量证明最低限额，固定
        if msg_method == 25:
            single_proof_gas_usage = 0
        if msg_method == 26:
            single_proof_gas_usage = 65733297  # 单扇区证明gas费率，固定

    bath_gas_fee = max(batch_balancer, base_fee)  # 批量gasFee = 批量证明最低限额与消息对应高度baseFee的最大值
    bath_gas_charge = bath_gas_fee * single_proof_gas_usage * sector_numbers * batch_discount
    return bath_gas_charge


class Validator(object):
    """通用参数验证器"""

    def validate_digit(self, number):
        # 验数字格式
        return True if re.match(
            r'^[-+]?(([0-9]+)([.]([0-9]+))?|([.]([0-9]+))?)$', number) else False

    def validate_email(self, email):
        # 验证邮箱格式
        return True if re.match(
            r'^[A-Za-z0-9-_]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email) else False

    def validate_mobile(self, mobile):
        # 验证手机号格式
        return True if re.match(r'^1\d{10}$', mobile) else False

    def validate_password(self, password):
        # 密码 8-16 位
        # return True if re.match(r'^([a-zA-Z0-9!@#$%^&*()_?<>{}]){8,16}$',
        # password) else False
        return True if re.match(r'^\S{8,16}$', password) else False

    def validate_date_time(self, date_str):
        # 验证日期（精确到秒）字符串
        if not isinstance(date_str, datetime.datetime):
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except BaseException:
                return False
        return True

    def validate_date(self, date_str):
        # 验证日期（精确到天）字符串
        if not isinstance(date_str, datetime.datetime):
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except BaseException:
                return False
        return True

    def validate_choice(self, choice, choice_list):
        '''
        验证选项是否有效
        '''
        return choice in [x[0] for x in choice_list]

    def validate_number(self, value, range_tuple):
        # 通用数值验证器，range_tuple为数值范围，左右闭包
        try:
            value = float(value)
        except BaseException:
            return False
        return range_tuple[0] <= value <= range_tuple[1]

    def validate_device_uuid(self, device_uuid):
        # 验证设备uuid
        return True if re.match(r'^\d{2}-.+$', device_uuid) else False

    def validate_bankcard(self, bankcard):
        '''
        验证银行卡号
        参考标准：https://pay.weixin.qq.com/wiki/doc/api/xiaowei.php?chapter=22_1
        '''
        return True if re.match(r'^[1-9]\d{9,29}$', bankcard) else False

    def validate_idcard(self, idcard):
        '''
        验证身份证
        '''
        rule = r'(^\d{8}(0\d|10|11|12)([0-2]\d|30|31)\d{3}$)|(^\d{6}(18|19|20)\d{2}(0\d|10|11|12)([0-2]\d|30|31)\d{3}(\d|X|x)$)'
        return True if re.match(rule, idcard) else False


def prams_filter(delete_key_list=[], **kargs):
    """
    过滤参数,只保留参数中非空,非none的部分
    :param delete_key_list:不过滤的参数
    :param args:
    :return:
    """
    result_dict = {}
    for key, value in dict(**kargs).items():
        if key in delete_key_list:
            continue
        if value is None or value == '""' or value == "":
            pass
        else:
            result_dict[key] = value
    return result_dict


def type_filter(type_filter=None, **kargs):
    """
    过滤选择型参数,如果传入的值为-9,那么不进行返回
    配合prams_filter一起使用
    :param type_filter: 需要删除过滤的字段 必须和数据库中的字段一致
    :param kargs:
    :return:不需要进行过滤的参数
    """
    result_list = []
    if isinstance(type_filter, list):
        for key in type_filter:
            if dict(**kargs).get(key) is None:
                return None, key
            elif dict(**kargs).get(key) == "-9":
                result_list.append(key)
    return result_list, False


from decimal import Decimal


def page_format(data, power=True, decimal=True):
    """
    将分页对象返回的data进行格式化返回
    :param data: 分页对象返回的data
    :param power:是否含有算力项
    :return:
    """
    if power or decimal:
        result_list = []
        for line in list(data['objects'].values()):
            # for key, value in line.items():
            #     # 算力转换--目前仅转换power字段,可能的字段多的话改成列表处理
            #     if key in ["power", "raw_power", "total_power", 'max_store']:
            #         line[key] = format_power(line[key])
            #     # 小数精度保留
            #     if isinstance(line[key], Decimal):
            #         line[key] = round(value, 2)
            # 算力转换
            # line['power'] = format_power(line['power'])
            result_list.append(line)
        return {
            'objs': result_list,
            'total_page': data['total_page'], 'total_count': data['total_count']
        }

    else:
        return {
            'objs': list(data['objects'].values()) if list(data['objects'].values()) != [] else [],
            'total_page': data['total_page'], 'total_count': data['total_count']
        }


def serializer_create_or_update(serializer, need_obj=False):
    """

    :param serializer: 序列化器
    :param need_obj: 是否需要返回对象
    :return:
    """
    flag = serializer.is_valid()
    if not flag:
        try:
            return format_return(15020, msg=str(serializer.errors[list(serializer.errors.keys())[0]][0]),
                                 data={"错误字段": list(serializer.errors.keys())[0]})
        except:
            return format_return(15020, msg=str(serializer._errors[0]),
                                 data={"错误字段": serializer._errors[0].code})

    result = serializer.save()
    if not need_obj:
        return format_return(0, data={'obj_id': result.id})
    else:
        return format_return(0, data={'obj_id': result.id, "obj": result})


def create_serial_number(user_pk):
    """
    生成交易流水号
    时间戳+userinfo表主键id,固定16位
    """
    timestamp = int(time.time() * 1000)
    return int(str(timestamp) + "%06d" % user_pk)


def format_float_coin(coin, point=3, flag=Decimal(10 ** -5)):
    """
    格式化coin的值,删除末尾的0,前进单位
    """
    # units = ["femto", "pico", "nano", "micro", "milli", ""]
    units = ["atto", "nano", ""]
    unit_index = 0

    power = decimal.Decimal(coin)
    temp = power / 10 ** 9
    while not (temp < flag) and (unit_index < len(units) - 1):
        unit_index += 1
        temp = temp / 10 ** 9
    temp *= 10 ** 9
    return '%s %s' % (format_price(temp, point=point), units[unit_index])


def format_coin_to_str(power, temp_value=10 ** 9, abandon=False, carry=6):
    '''
    temp:判断需要小于多少
    格式化power
    carry:向前进位参数   10**carry次方后再向前进位
    '''
    # units = ["femto", "pico", "nano", "micro", "milli", ""]
    units = ["atto", "nano", ""]
    unit_index = 0

    power = abs(decimal.Decimal(power))
    if power < 10 ** carry and abandon:
        return 0
    if power < 10 ** carry:
        return '%s %s' % (format_price(power), units[unit_index])
    temp = power / 10 ** 9
    unit_index += 1
    while (temp >= temp_value) and (unit_index < len(units) - 1):
        temp = temp / 10 ** 9
        unit_index += 1

    return '%s %s %s' % ('-' if power < 0 else "", format_price(temp, 4), units[unit_index])


def _d(v):
    return decimal.Decimal(v)


def height_to_datetime(height, need_format=False):
    '''高度转换成时间'''
    launch_date = datetime.datetime(2020, 8, 25, 6, 0, 0)
    seconds = int(height) * 30
    d = launch_date + datetime.timedelta(seconds=seconds)
    return d.strftime('%Y-%m-%d %H:%M:%S') if need_format else d


def datetime_to_height(d=None):
    '''时间转换成高度'''
    launch_date = datetime.datetime(2020, 8, 25, 6, 0, 0)
    if d is None:
        temp = datetime.datetime.now().replace(microsecond=0)
    else:
        if isinstance(d, str):
            temp = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        elif isinstance(d, datetime.datetime):
            temp = d
        elif isinstance(d, datetime.date):
            temp = datetime.datetime.combine(d, datetime.time.min)
        else:
            return 0
    return int((temp - launch_date).total_seconds() / 30)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    选择需要序列化的字段进行序列化操作
    实例化时传入 fields={需要序列化的字段}
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


def parameter_verify(must_params_list, request_data_dict):
    """

    :param must_params_list:
    :param request_data_dict:
    :return:
    """
    for must_params in must_params_list:
        if not must_params in request_data_dict or must_params == "":
            return False, must_params
    return True, None


class VscodeBase:
    """
    发送短信验证码方法,对于每个手机号限制60秒发送一次
    每个验证码有效期5分钟
    """

    def __init__(self, method, content=None, limit_times=30):
        """

        :param method: 短信方法
        :param content: 短信内容
        :param limit_time: 每天短信次数限制
        """
        self.method = method
        self.redis_key = self.create_redis_key()
        self.frequency_key = self.create_frequency_key()
        self.sms_flag = self.redis_key + "flag"
        self.content = self.content_map(content)
        self.limit_time = limit_times

    def create_redis_key(self):
        return "v_code_" + self.method + "_%s"

    def create_frequency_key(self):
        return "day_v_" + self.method + "_%s_%s"

    def content_map(self, content_data):
        content = {
            "update_address": "验证码{}，5分钟后失效。您的操作需要进行校验，请勿泄露短信验证码。",
            "create_address": "验证码{}，5分钟后失效。您的操作需要进行校验，请勿泄露短信验证码。",
            "withdraw_deposit": "验证码{}，5分钟后失效。您的操作需要进行校验，请勿泄露短信验证码。",
            "change_psword": "验证码{}，5分钟后失效。您正在进行修改密码操作，请勿泄露短信验证码。",
            "reset_psword": "验证码{}，5分钟后失效。您正在进行重置密码操作，请勿泄露短信验证码。",
            "sms_login": "验证码{}，5分钟后失效。您正在进行登录操作，请勿泄露短信验证码。",
            "register": "验证码{}，5分钟后失效。您正在进行注册操作，请勿泄露短信验证码。",
            "change_mobile": "验证码{}，5分钟后失效。您正在进行更换手机操作，请勿泄露短信验证码",
        }
        return content.get(self.method) if content.get(self.method) else content_data

    def send_code(self, mobile, content, **kwargs):
        '''
        发送验证码
        '''
        try:
            # ==== 直接调用api
            # from jm_common.yunpian_sms_sdk import YunPianSms
            # YunPianSms().send_vercode(mobile, code)
            from explorer_s_common.mq.mq_kafka import Producer, MQ_TOPIC_SEND_SMS

            # ==== 使用 kafka
            # 验证手机号是否为海外用户,开头为00的号码为海外用户,海外用户需要使用海外渠道进行注册
            if str(mobile)[:2] == "00":
                data = {'mobile': mobile, 'content': content, "product_id": 1012809, **kwargs}
            else:
                data = {'mobile': mobile, 'content': content, **kwargs}
            # content = "验证码%s，欢迎注册/登录一石云池，请勿泄露短信验证码。【一石云池】" % code
            Producer().send(MQ_TOPIC_SEND_SMS, data)
        except Exception as e:
            debug.get_debug_detail(e)

    def generate_code(self, mobile, ver_key=False):
        '''
        生成验证码
        '''

        cache_obj = Cache()
        code = cache_obj.get(self.redis_key % (mobile))

        # 缓存是否存在
        if not code:
            code = str(random.randint(100000, 999999))
            cache_obj.set(self.redis_key % (mobile), code, 5 * 60)  # 有效期5分钟
            cache_obj.set(self.sms_flag % (mobile), code, 60)  # 发送短信间隔
            print("生成验证码为:{}".format(code))
            return code
        else:
            # 存在的话查询是否频繁发送短信了
            flag = cache_obj.get(self.sms_flag % (mobile))
            if flag:
                return None
            else:
                code = str(random.randint(100000, 999999))
                cache_obj.set(self.redis_key % (mobile), code, 5 * 60)  # 有效期5分钟
                cache_obj.set(self.sms_flag % (mobile), code, 60)  # 发送短信间隔
                return code

    def check_can_send_vercode(self, mobile):
        '''
        检测是否超出限制
        '''
        day = datetime.datetime.now().strftime('%Y-%m-%d')
        key = self.frequency_key % (mobile, day)
        cache_obj = Cache()
        count = cache_obj.get(key) or 0
        print('key, count=>', key, count)
        if count >= self.limit_time:
            return False

        # 次数+1
        cache_obj.set(key, count + 1, 24 * 60 * 60)
        return True

    def ver_code(self, verification_code, mobile):
        """
        校验验证码
        """
        cache_obj = Cache()
        code = cache_obj.get(self.redis_key % (mobile))
        if verification_code == code:
            # 验证通过删除验证码
            cache_obj.delete(self.redis_key % (mobile))
            return True


class FilterQueryset(QuerySet):
    """查询时默认只查询状态为1的数据"""

    def filter(self, *args, state=1, **kwargs):
        """
        Return a new QuerySet instance with the args ANDed to the existing
        set.
        """
        self._not_support_combined_queries('filter')
        return self._filter_or_exclude(False, state=state, *args, **kwargs)


class FilterManager(BaseManager.from_queryset(FilterQueryset)):
    pass


# 模型类校验器
@deconstructible
class MinValueValidatorEqual(BaseValidator):
    message = _('请确保输入的值大于等于 %(limit_value)s.')
    code = 'min_value'

    def compare(self, a, b):
        return a < b


@deconstructible
class MaxValueValidatorEqual(BaseValidator):
    message = _('请确保输入的值小于等于 %(limit_value)s.')
    code = 'max_value'

    def compare(self, a, b):
        return a > b


def format_es_fil_data(init_data, need_round=False, round_precision=4):
    """
    #对于es中钱包的数据进行格式化
    :param init_data:es中查询出的数据
    :param need_round:是否需要保留小数
    :param round_precision:保留小数的位数
    :return:
    """
    filed_list = ['initial_pledge', 'locked_funds', 'initial_pledge', 'available_balance_value', 'total_balance_value',
                  'owner_balance_value', 'worker_balance_value', 'post_balance_value']
    result_dict = {}
    for key, value in init_data.items():
        result_dict[key] = value
        if key in filed_list:
            # 如果key里面找到了value部分,那么删除_value(从后向前)
            if key.find("_value") != -1:
                if need_round:
                    result_dict[key.replace("_value", "")] = round(int(value) / 10 ** 18, round_precision)
                else:
                    result_dict[key.replace("_value", "")] = int(value) / 10 ** 18
            # 否则添加_value为字符串后的数据
            else:
                if need_round:
                    result_dict[key + "_value"] = round(int(value) / 10 ** 18, round_precision)
                else:
                    result_dict[key + "_value"] = int(value) / 10 ** 18
    return result_dict
