import os
import datetime
import logging
import requests
import threading
from functools import wraps
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(
    format='%(levelname)s:%(asctime)s %(pathname)s--%(funcName)s--line %(lineno)d-----%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)


def func_log(func):
    '''
    记录操作信息
    '''

    @wraps(func)
    def wrapper(*args, **kwargs):

        thread_id = threading.get_ident()
        start_time = datetime.datetime.now()
        logging.warning('[== %s ==]开始执行方法[ %s ]' % (thread_id, func.__name__))
        try:
            result = func(*args, **kwargs)
            logging.warning(result)
        except Exception as e:
            print(e)
            result = {"code": 99904, "msg": "系统错误"}
        end_time = datetime.datetime.now()
        cost_time = end_time - start_time
        logging.warning('[== %s ==]方法[ %s ]执行结束，耗时[ %s ]s' % (thread_id, func.__name__, cost_time.total_seconds()))

        return result

    return wrapper


@func_log
def sync_tipset():
    '''同步区块一天一次'''
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    url = os.getenv('SERVER_DATA') + '/data/api/tipset/sync_tipset'
    return requests.post(url=url, timeout=600, data={'date': yesterday_str}).json()


@func_log
def sync_temp_tipset():
    '''同步24小时区块3分钟一次'''
    url = os.getenv('SERVER_DATA') + '/data/api/tipset/sync_temp_tipset'
    return requests.post(url=url, timeout=600).json()


@func_log
def sync_active_miners():
    '''同步活跃矿工一天一次'''
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_active_miners'
    return requests.post(url=url, timeout=600).json()


@func_log
def sync_pool_miners():
    '''同步矿池矿工10分钟一次'''
    now = datetime.datetime.now()
    temp = now.replace(hour=0, minute=0, second=0)
    # 3点之前不同步
    if (now - temp).total_seconds() <= (3 * 60 * 60):
        return
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_pool_miners'
    return requests.post(url=url, timeout=600).json()


@func_log
def sync_miner_day_stat():
    '''同步矿工当天状态'''
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_miner_day_stat'
    return requests.post(url=url, timeout=600, data={'date': yesterday_str}).json()


@func_log
def sync_miner_total_stat():
    '''同步矿工总状态'''
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_miner_total_stat'
    return requests.post(url=url, timeout=600).json()


@func_log
def sync_miner_history():
    '''同步矿工历史'''
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_miner_history'
    return requests.post(url=url, timeout=600, data={'date': yesterday_str}).json()


@func_log
def sync_miner_day_gas():
    '''同步矿工gas'''
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_miner_day_gas'
    return requests.post(url=url, timeout=600, data={'date': yesterday_str}).json()


@func_log
def sync_miner_day_overtime_pledge_fee():
    # 同步每日浪费质押gas
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_miner_day_overtime_pledge_fee'
    return requests.post(url=url, timeout=600).json()


@func_log
def get_overview():
    '''同步全网概览'''
    url = os.getenv('SERVER_DATA') + '/data/api/overview/get_overview'
    return requests.post(url=url, timeout=60, data={'must_update_cache': '1'}).json()


@func_log
def get_pool_overview():
    '''同步矿池概览'''
    url = os.getenv('SERVER_DATA') + '/data/api/overview/get_pool_overview'
    return requests.post(url=url, timeout=60, data={'must_update_cache': '1'}).json()


@func_log
def sync_tipset_gas():
    '''同步单个区块gas汇总'''
    url = os.getenv('SERVER_DATA') + '/data/api/message/sync_tipset_gas'
    return requests.post(url=url, timeout=600, data={}).json()


@func_log
def sync_deal():
    '''同步新增订单'''
    url = os.getenv('SERVER_DATA') + '/data/api/deal/sync_deal'
    return requests.post(url=url, timeout=600, data={}).json()


@func_log
def sync_explorer_index():
    '''计算浏览器昨日指数'''
    miner_url = os.getenv('SERVER_EXPLORER') + '/explorer/api/exponent/sync_data_miner'
    company_url = os.getenv('SERVER_EXPLORER') + '/explorer/api/exponent/sync_data_miner_company'
    miner_response = requests.post(url=miner_url, timeout=3600, data={}).json()
    company_response = requests.post(url=company_url, timeout=3600, data={}).json()
    return miner_response, company_response


@func_log
def sync_miner_tag():
    """更新标签"""
    url = os.getenv('SERVER_EXPLORER') + '/explorer/api/master_overview/sync_miner_tag'
    response = requests.post(url=url, timeout=3600, data={}).json()
    return response


@func_log
def sync_explorer_fil_index_0():
    '''同步fil指数任务'''
    url = os.getenv('SERVER_EXPLORER') + '/explorer/api/index/update0'
    return requests.post(url=url, timeout=600, data={}).json()


@func_log
def sync_explorer_fil_index_8():
    '''同步fil指数任务'''
    url = os.getenv('SERVER_EXPLORER') + '/explorer/api/index/update8'
    return requests.post(url=url, timeout=600, data={}).json()

@func_log
def sync_miner_lotus():
    '''同步链上数据'''
    url = os.getenv('SERVER_DATA') + '/data/api/miner/sync_miner_lotus'
    return requests.post(url=url, timeout=600).json()

# @func_log
# def sync_miner_day_overtime_pledge_fee_by_last_7days():
#     # 同步之前7日浪费质押gas
#     ret = dict()
#     today = datetime.datetime.today()
#     for i in range(1, 8):
#         date = today - datetime.timedelta(days=i)
#         date = date.strftime('%Y-%m-%d')
#         request_dict = dict(date=date)
#         url = '%s/data/api/miner/sync_miner_day_overtime_pledge_fee' % os.getenv('SERVER_DATA')
#         resp = requests.post(url=url, timeout=600, data=request_dict).json()
#         ret[date] = resp
#     return ret


@func_log
def sync_overtime_pledge():
    '''计算最近的过期质押'''
    url = os.getenv('SERVER_DATA') + '/data/api/message/sync_overtime_pledge'
    return requests.post(url=url, timeout=600, data={}).json()


if __name__ == '__main__':
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    # scheduler.add_job(func=aps_test, args=('定时任务',), trigger='cron', second='*/5')
    # scheduler.add_job(func=aps_test, args=('一次性任务',), next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=12))
    # scheduler.add_job(func=aps_test, args=('循环任务',), trigger='interval', seconds=3)
    scheduler.add_job(func=sync_tipset, trigger='cron', hour=0, minute=1)
    scheduler.add_job(func=sync_temp_tipset, trigger='cron', second='*/30')
    scheduler.add_job(func=sync_active_miners, trigger='cron', minute='*/10')
    # scheduler.add_job(func=sync_pool_miners, trigger='cron', minute='*/10')
    # scheduler.add_job(func=sync_miner_day_stat, trigger='cron', hour=2, minute=35)
    scheduler.add_job(func=sync_miner_total_stat, trigger='cron', minute='*/10')
    scheduler.add_job(func=sync_miner_history, trigger='cron', hour=0, minute=10)
    scheduler.add_job(func=sync_miner_day_gas, trigger='cron', hour=3, minute=40)
    scheduler.add_job(func=sync_miner_day_overtime_pledge_fee, trigger='cron', hour=7, minute=10)  # 同步每日浪费质押gas
    scheduler.add_job(func=get_overview, trigger='cron', second='*/30')
    scheduler.add_job(func=get_pool_overview, trigger='cron', minute='*/10')
    scheduler.add_job(func=sync_tipset_gas, trigger='cron', minute='*/5')
    scheduler.add_job(func=sync_overtime_pledge, trigger='cron', minute='*/10')
    scheduler.add_job(func=sync_deal, trigger='cron', minute='*/30')
    scheduler.add_job(func=sync_explorer_index, trigger='cron', hour=1, minute=45)  # 计算浏览器昨日指数
    scheduler.add_job(func=sync_miner_tag, trigger='interval', seconds=60 * 60 * 6)  # 更新浏览器标签
    scheduler.add_job(func=sync_explorer_fil_index_0, trigger='cron', hour=0, minute=1)  # 计算fil昨日指数
    scheduler.add_job(func=sync_explorer_fil_index_8, trigger='cron', hour=8, minute=1)  # 计算fil昨日指数
    scheduler.add_job(func=sync_miner_lotus, trigger='cron', hour=5, minute=1)
    # scheduler.add_job(func=sync_miner_day_overtime_pledge_fee_by_last_7days, trigger='cron', hour=3, minute=1)  # 同步最近7日浪费质押gas
    scheduler.start()
