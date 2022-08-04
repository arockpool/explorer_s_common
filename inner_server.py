import requests
import datetime
import logging
import json

from explorer_s_common import debug, consts, cache, decorator


def fetch(url, data={}, headers={}, response_log=True):
    try:
        logging.warning('url--> %s' % url)
        logging.warning('data--> %s' % data)
        result = requests.post(url, headers=headers, data=data, timeout=60).json()
        if response_log:
            logging.warning('response--> %s' % result)
        return result
    except Exception as e:
        debug.get_debug_detail(e)
        return {'code': 99904, 'data': {}, 'msg': ''}


def add_request_log(data={}):
    '''
    添加访问日志
    '''
    url = '%s/system/api/monitor/add_request_log' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def add_slow_request(request_url, duration, ip, post_data):
    '''
    添加慢请求
    '''
    url = '%s/system/api/monitor/add_slow_request' % (consts.SERVER_SYSTEM)
    data = {'url': request_url, 'duration': duration, 'ip': ip, 'post_data': post_data}
    return fetch(url=url, headers={}, data=data)


def add_sys_error(service, request_url, detail):
    '''
    添加慢请求
    '''

    url = '%s/system/api/monitor/add_sys_error' % (consts.SERVER_SYSTEM)
    data = {'service': service, 'url': request_url, 'detail': detail}
    return fetch(url=url, headers={}, data=data)


def get_app_info(app_id):
    '''
    获取appinfo
    '''
    cache_obj = cache.Cache(config=cache.CACHE_API)
    cache_key = 'app_info_%s' % app_id
    app_info = cache_obj.get(cache_key)

    # 如果命中缓存
    if app_info:
        return app_info
    else:
        url = '%s/system/api/get_app_info' % (consts.SERVER_SYSTEM)
        data = fetch(url=url, data={"app_id": app_id})
        if data.get('code') == 0:
            cache_obj.set(cache_key, data, time_out=3600)
        return data


def get_user_profile(user_id):
    '''
    获取个人信息
    '''
    cache_obj = cache.Cache(config=cache.CACHE_ACCOUNT)
    cache_key = 'user_profile_%s' % user_id
    profile = cache_obj.get(cache_key)

    # 如果命中缓存
    if profile:
        return profile
    else:
        url = '%s/profile/api/get_user_profile' % (consts.SERVER_PROFILE)
        return fetch(url=url, headers={"USERID": user_id})['data']


def update_profile_for_register(user_id, data={}):
    '''
    注册后修改用户资料
    '''
    url = '%s/profile/api/update_profile_for_register' % (consts.SERVER_PROFILE)
    return fetch(url=url, headers={"USERID": user_id}, data=data)


def add_profile(user_id, data={}):
    '''
    添加用户资料
    '''
    url = '%s/profile/api/add_profile' % (consts.SERVER_PROFILE)
    return fetch(url=url, headers={"USERID": user_id}, data=data)


def register(data={}):
    '''
    授权账号
    '''
    url = '%s/account/api/register' % (consts.SERVER_ACCOUNT)
    return fetch(url=url, data=data)


def register_or_update(data={}):
    '''
    更新或者注册用户信息
    '''
    url = '%s/account/api/register_or_update' % (consts.SERVER_ACCOUNT)
    return fetch(url=url, data=data)


def get_company_admin_by_miner_no(data={}):
    '''
    根据矿工号获取账号的管理员
    '''
    url = '%s/pool/api/company/get_company_admin_by_miner_no' % (consts.SERVER_POOL)
    return fetch(url=url, data=data)


def get_user_id_by_mobile(data={}):
    """
    根据手机号获取user_id
    :param data:
    :return:
    """
    url = '%s/profile/admin/get_user_by_mobile' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


def get_user_login_info_by_user_id(data={}):
    """
    根据user_id,查询用户最后登录时间,创建时间
    :param data:
    :return:
    """
    url = '%s/account/api/get_user_login_info_by_user_id' % (consts.SERVER_ACCOUNT)
    return fetch(url=url, data=data)


def get_user_all_list(data={}):
    """
    获取user的全部信息
    :param data:
    :return:
    """
    url = '%s/profile/admin/get_user_all_list' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


# def get_user_id_by_mobile_account(data={}):
#     """
#     暂时不使用该接口,使用get_miner_user_id_by_mobile_profile代替本功能(丢失最后登录时间字段)
#     根据手机号获取user_id
#     :param data:
#     :return:
#     """
#     url = '%s/account/api/get_user_info_by_mobile' % (consts.SERVER_ACCOUNT)
#     return fetch(url=url, data=data)

def get_miner_user_id_by_mobile_profile(data={}):
    """
    根据手机号获取user_id
    :param data:
    :return:
    """
    url = '%s/profile/api/get_miner_user_info_by_mobile' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


def creat_user_info(data={}):
    """
    注册父级用户时,注册到user_info中
    :param data:
    :return:
    """
    url = '%s/pool/api/company/creat_user_info' % (consts.SERVER_POOL)
    return fetch(url=url, data=data)


def register_super_user(data={}):
    """
    注册超级管理员
    :param data:
    :return:
    """
    url = '%s/system/admin/add_admin_super_super' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def get_admin_user_id_list(data={}):
    """
    获得管理员列表
    :param data:
    :return:
    """
    url = '%s/system/admin/get_admin_user_id_list' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def del_user_form_account(data={}):
    """
    account删除用户
    :param data:
    :return:
    """
    url = '%s/account/admin/del_user' % (consts.SERVER_ACCOUNT)
    return fetch(url=url, data=data)


def del_user_form_profile(data={}):
    """
    profile删除用户
    :param data:
    :return:
    """
    url = '%s/profile/admin/delete_user' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


def send_sms(data={}):
    '''
    发送短信
    '''
    url = '%s/system/api/send_sms' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def send_email(data={}):
    '''
    发送邮件
    '''
    url = '%s/system/api/send_email' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def get_calculate_info(data={}):
    '''
    获取file概览
    '''
    url = '%s/activity/api/calculator/get_calculate_info' % (consts.SERVER_ACTIVITY)
    return fetch(url=url, data=data)


def get_calculator_get_lookups(data={}):
    '''
    获取出块预测
    '''
    url = '%s/activity/api/calculator/viewer/get_lookups' % (consts.SERVER_ACTIVITY)
    return fetch(url=url, data=data)



def get_online_miner_info(data={}):
    '''
    线上矿工数据
    '''
    url = '%s/explorer/api/address/%s/overview' % (consts.SERVER_EXPLORER, data.get("miner_id"))
    print(url)
    return fetch(url=url, data=data)


def get_online_miner_powers_state(data={}):
    '''
    线上矿工算力变化
    '''
    url = '%s/explorer/api/address/%s/power-stats' % (consts.SERVER_EXPLORER, data.get("miner_id"))
    print(url)
    return fetch(url=url, data=data)


def get_add_admin_by_role(data={}):
    '''
    管理员添加权限
    '''
    url = '%s/system/admin/add_admin_by_role' % (consts.SERVER_SYSTEM)
    print(url)
    return fetch(url=url, data=data)


def get_gas_stat_all(data={}):
    '''
    获取gas统计
    '''
    url = '%s/data/api/message/get_gas_stat_all' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_base_fee_trends(data={}):
    '''
    获取base_fee统计
    '''
    url = '%s/data/api/message/get_base_fee_trends' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_gas_cost_stat(data={}):
    '''
    获取gas消耗统计接口
    '''
    url = '%s/data/api/message/get_gas_cost_stat' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_message_detail(data={}):
    '''
    获取消息详情
    '''
    url = '%s/data/api/message/get_message_detail' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_net_ovewview(data={}):
    '''
    获取全网数据概览
    '''

    url = '%s/data/api/overview/get_overview' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_net_ovewview_day_records(data={}):
    '''
    获取全网数据概览
    '''
    url = '%s/data/api/overview/get_overview_day_records' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_list(data={}, response_log=False):
    '''
    获取有效算力排名
    '''


    url = '%s/data/api/miner/get_miner_list' % (consts.SERVER_DATA)
    return fetch(url=url, data=data, response_log=response_log)


def get_miner_list_by_miners(data={}):
    '''
    获取miner列表
    '''
    url = '%s/data/api/miner/get_miner_list_by_miners' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)

def get_miner_list_by_power_inc(data={}):
    '''
    获取算力增速排名
    '''
    url = '%s/data/api/miner/get_miner_list_by_power_inc' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_list_by_power_inc_24(data={}):
    '''
    # 根据24小时封装量  获取算力增速排名
    '''
    url = '%s/data/api/miner/get_miner_list_by_power_inc_24' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_list_by_block(data={}):
    '''
    获取出块排名
    '''
    url = '%s/data/api/miner/get_miner_list_by_block' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_list_by_avg_reward(data={}):
    '''
    根据挖矿效率排名
    '''

    url = '%s/data/api/miner/get_miner_list_by_avg_reward' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_list_by_avg_reward_for_month_avg(data={}):
    '''
    根据挖矿效率排名
    '''

    url = '%s/data/api/miner/get_miner_list_by_avg_reward_for_month_avg' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_list_by_avg_reward_24(data={}):
    '''
    根据24挖矿效率排名
    '''

    url = '%s/data/api/miner/get_miner_list_by_avg_reward_24' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_tipsets(data={}):
    '''
    获取出块信息
    '''
    url = '%s/data/api/tipset/get_tipsets' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_by_no(data={}):
    '''
    获得矿工详情
    '''
    url = '%s/data/api/miner/get_miner_by_no' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_tipset_by_height(data={}):
    '''
    获取出块信息详情
    '''
    url = '%s/data/api/tipset/get_tipset_by_height' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_memory_pool_message(data={}):
    '''
    获取内存池消息列表
    '''
    url = '%s/data/api/message/get_memory_pool_message' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


# def get_transfer_list(data={}):
#     '''
#     获取用户转账列表
#     '''
#     url = '%s/data/api/message/get_transfer_list' % (consts.SERVER_DATA)
#     return fetch(url=url, data=data)


def get_miner_day_records(data={"page_size": 100, "page_index": 1}, response_log=False):
    """
    按天获取矿工历史数据
    :param data: 数据参数
        date:历史数据日期,默认为昨日
        page_index:页面索引
        page_size:每页数据量
        miner_no:矿工号
    :return:
    """

    url = '%s/data/api/miner/get_miner_day_records' % (consts.SERVER_DATA)
    return fetch(url=url, data=data, response_log=response_log)


def get_company_miner_mapping(data={}):
    url = '%s/data/api/miner/get_company_miner_mapping' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_to_company_mapping(data={}):
    """
    获取miner_company对应关系
    :return:
    """
    url = '%s/data/api/miner/get_miner_to_company_mapping' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_blocks(data={}):
    """
    获得用户出块列表
    :return:
    """
    url = '%s/data/api/tipset/get_miner_blocks' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_block_detail(data={}):
    """
    获得用户出块列表
    :return:
    """
    url = '%s/data/api/tipset/get_block_detail' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_block_message(data={}):
    """
    获得用户出块列表
    :return:
    """
    url = '%s/data/api/tipset/get_block_message' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_message_list(data={}):
    """
    获得用户消息列表
    :return:
    """
    url = '%s/data/api/message/get_message_list' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_deal_stat(data={}):
    """
    获得用户消息列表
    :return:
    """
    url = '%s/data/api/deal/get_deal_stat' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_user_by_id(data={}):
    """
    根据user_id获得用户信息
    :return:
    """
    url = '%s/profile/admin/get_user_by_id' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


def get_148888_active_miners(data={}, response_log=True):
    """
    获得14888高度时的初始值
    :param data:
    :return:
    """

    url = '%s/data/api/miner/get_148888_active_miners' % (consts.SERVER_DATA)
    return fetch(url=url, data=data, response_log=response_log)


def get_user_pool_kind(data={}):
    url = '%s/pool/api/company/v3/get_user_kind' % (consts.SERVER_POOL)
    return fetch(url=url, data=data)


def get_pool_miner_detail(data={}):
    url = '%s/data/api/miner/get_pool_miner_detail' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_pool_activate_miner_detail(data={}):
    url = '%s/data/api/miner/get_pool_activate_miner_detail' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_pool_attention_miner_detail(data={}):
    url = '%s/data/api/miner/get_pool_attention_miner_detail' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_usd_rate(data={}):
    url = '%s/activity/api/calculator/get_usd_rate' % (consts.SERVER_ACTIVITY)
    return fetch(url=url, data=data)


def get_super_admin_user_id_list(data={}):
    url = '%s/system/admin/get_super_admin_user_id_list' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def get_role_user_id(data={}):
    url = '%s/system/admin/get_role_user_id' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def get_user_profile_by_user_id(data={}):
    url = '%s/profile/api/get_user_profile_by_user_id' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


def get_init_value(data={}):
    url = '%s/data/api/miner/get_init_value' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_increment(data={}):
    """获得所有信息增量"""
    url = '%s/data/api/miner/get_miner_increment' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def delete_user_account(data={}):
    """删除用户account(物理删除)"""
    url = '%s/account/api/delete_user_account' % (consts.SERVER_ACCOUNT)
    return fetch(url=url, data=data)


def delete_user_profile(data={}):
    """删除用户profile(物理删除)"""
    url = '%s/profile/api/delete_user_profile' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


def get_config(data={}):
    """获得配置相关"""
    url = '%s/system/admin/get_config' % (consts.SERVER_SYSTEM)
    return fetch(url=url, data=data)


def get_parent_user_system(data={}):
    """获得手机号的父用户配置相关(目前仅返回短信相关)"""
    url = '%s/pool/api/company/v3/get_parent_user_system' % (consts.SERVER_POOL)
    return fetch(url=url, data=data)


def get_user_info_by_thirdapp(external_user_id, source):
    '''
    根据第三方id获取用户信息
    '''
    url = '%s/account/api/get_user_info_by_thirdapp' % (consts.SERVER_ACCOUNT)
    return fetch(url=url, headers={}, data={'external_user_id': external_user_id, 'source': source})


def get_miner_day_record(data={}):
    url = '%s/data/api/rmd/get_miner_day_record' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def register_by_thirdapp(data={}):
    """
    第三方注册
    """
    url = '%s/account/api/register_by_thirdapp' % (consts.SERVER_ACCOUNT)
    return fetch(url=url, data=data)


def get_history_day_records(data={}):
    """
    获得历史全网数据概览
    """
    url = '%s/data/api/overview/get_history_day_records' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_mining_stats_by_no(data={}):
    """
    获取矿工生产统计
    """
    url = '%s/data/api/miner/get_miner_mining_stats_by_no' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_line_chart_by_no(data={}):
    """
    矿工算力和出口图数据
    """
    url = '%s/data/api/miner/get_miner_line_chart_by_no' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_deal_list(data={}):
    """
    获取订单列表
    """
    url = '%s/data/api/deal/deal_list' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_deal_info(data={}):
    """
    获取订单详情
    """
    url = '%s/data/api/deal/deal_info' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_gas_sum_by_per(data={}):
    """
    全网生产gas
    """
    url = '%s/data/api/message/get_gas_sum_by_per' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_health_report_24h_by_no(data={}):
    '''
    节点健康报告24H详情
    '''

    url = '%s/explorer_v2/miner/get_miner_health_report_24h_by_no' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def get_overview_day_list(data={}):
    '''
    获取全网数据概览按天
    '''
    url = '%s/explorer_v2/stat/get_overview_day_list' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def get_overview_stat(data={}):
    '''
    获取全网数据概览
    '''
    url = '%s/explorer_v2/stat/get_overview_stat' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)

def get_miner_health_report_day_by_no(data={}):
    '''
    节点健康报告7天列表
    '''

    url = '%s/explorer_v2/miner/get_miner_health_report_day_by_no' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def get_miner_health_report_gas_stat_by_no(data={}):
    '''
    节点健康报告gas分析
    '''

    url = '%s/explorer_v2/miner/get_miner_health_report_gas_stat_by_no' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def get_messages_stat_by_miner_no(data={}):
    '''
    节点健康报告消息分析
    '''

    url = '%s/explorer_v2/miner/get_messages_stat_by_miner_no' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def set_explorer_mobile(data={}):
    """
    设置用户手机号(浏览器)
    """
    url = '%s/explorer/api/pro/set_explorer_mobile' % (consts.SERVER_EXPLORER)

    return fetch(url=url, data=data)

def invite_user(data={}):
    """
    邀請用戶活動(浏览器)
    """
    url = '%s/explorer/api/pro/invite_user' % (consts.SERVER_EXPLORER)

    return fetch(url=url, data=data)


def set_profile_mobile(data={}):
    """
    设置用户手机号
    """
    url = '%s/profile/admin/set_profile_mobile' % (consts.SERVER_PROFILE)
    return fetch(url=url, data=data)


def set_pool_mobile(data={}):
    """
    设置用户手机号（矿池）
    """
    url = '%s/pool/admin/company/set_user_info_mobile' % (consts.SERVER_POOL)
    return fetch(url=url, data=data)


def get_wallet_address_estimated_service_day(data={}):
    """
    根据miner no 计算钱包剩余day
    """
    url = '%s/explorer_v2/miner/get_wallet_address_estimated_service_day' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def get_miner_apply_tag(data={}):
    """
    根据miner no 计算钱包剩余day
    """
    url = '%s/explorer/api/master_overview/get_miner_apply_tag' % (consts.SERVER_EXPLORER)
    return fetch(url=url, data=data)


def deal_all_list(data={}):
    """
    根据miner no 计算钱包剩余day
    """
    url = '%s/data/api/deal/deal_all_list' % (consts.SERVER_DATA)
    return fetch(url=url, data=data)


def get_miner_ranking_list_by_power(data={}, response_log=False):
    '''
    获取有效算力排名
    '''
    url = '%s/explorer_v2/homepage/get_miner_ranking_list_by_power' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data, response_log=response_log)


def get_miner_ranking_list(data={}, response_log=False):
    '''
    获取有效算力排名
    '''
    url = '%s/explorer_v2/homepage/get_miner_ranking_list' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data, response_log=response_log)


def get_wallets_list(data={}, response_log=False):
    '''
    钱包列表
    '''
    url = '%s/explorer_v2/block_chain/get_wallets_list' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data, response_log=response_log)


def get_wallet_address_change(data={}, response_log=False):
    '''
    查询钱包的具体改变值
    '''
    url = '%s/explorer_v2/inner/get_wallet_address_change' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data, response_log=response_log)


def get_wallet_info(data={}, response_log=False):
    '''
    查询钱包的具体改变值
    '''
    url = '%s/explorer_v2/block_chain/get_wallet_info' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data, response_log=response_log)


def get_miner_by_miner_no(data={}):
    '''
    获得矿工详情
    '''
    url = '%s/explorer_v2/miner/get_miner_by_no' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def get_miner_stats_by_no(data={}):
    '''
    获得矿工产出详情
    '''
    url = '%s/explorer_v2/miner/get_miner_stats_by_no' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)


def get_transfer_list(data={}):
    '''
    获取用户转账列表
    '''
    url = '%s/explorer_v2/miner/get_transfer_list' % (consts.SERVER_EXPLORER_V2)
    return fetch(url=url, data=data)
