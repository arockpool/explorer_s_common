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
def sync_overview():
    url = os.getenv('SERVER_POOL') + '/pool/api/browser/sync_overview'
    return requests.post(url=url, data={'net': 'spacerace'}, timeout=30).json()


@func_log
def sync_miner_ranking():
    url = os.getenv('SERVER_POOL') + '/pool/api/browser/sync_miner_ranking'
    return requests.post(url=url, data={'net': 'spacerace'}, timeout=30).json()


@func_log
def sync_miner_increase_ranking():
    url = os.getenv('SERVER_POOL') + '/pool/api/browser/sync_miner_increase_ranking'
    return requests.post(url=url, data={'net': 'spacerace'}, timeout=30).json()


@func_log
def sync_block_ranking():
    url = os.getenv('SERVER_POOL') + '/pool/api/browser/sync_block_ranking'
    return requests.post(url=url, data={'net': 'spacerace'}, timeout=30).json()


@func_log
def sync_balance_ranking():
    url = os.getenv('SERVER_POOL') + '/pool/api/browser/sync_balance_ranking'
    return requests.post(url=url, data={'net': 'spacerace'}, timeout=30).json()


@func_log
def sync_block_list():
    url = os.getenv('SERVER_POOL') + '/pool/api/browser/sync_block_list'
    return requests.post(url=url, data={'net': 'spacerace'}, timeout=30).json()


@func_log
def sync_power_increase():
    url = os.getenv('SERVER_POOL') + '/pool/api/browser/sync_power_increase'
    requests.post(url=url, data={'net': 'spacerace', 'ranking_type': 'quality'}, timeout=30).json()
    return requests.post(url=url, data={'net': 'spacerace', 'ranking_type': 'row'}, timeout=30).json()


@func_log
def sync_calculator_total_power_per_hour():
    '''定时存储全网总算力'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/calculator/sync_total_power_per_hour'
    return requests.post(url=url, data={}, timeout=30).json()


@func_log
def sync_calculator_tipset():
    '''定时更新tipset'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/calculator/sync_tipset'
    return requests.post(url=url, data={}, timeout=60 * 60).json()


@func_log
def sync_calculator_temp_tipset():
    '''定时更新临时tipset'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/calculator/sync_temp_tipset'
    return requests.post(url=url, data={}, timeout=60 * 60).json()


@func_log
def sync_calculator_lookups():
    '''定时更新对照表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/calculator/viewer/get_lookups'
    return requests.post(url=url, data={'must_update_cache': '1', 'luck_v': '0.997'}, timeout=10 * 60).json()


@func_log
def sync_calculator_gas_fee():
    '''定时更新汽油费表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/calculator/sync_gas_fee'
    return requests.post(url=url, data={}, timeout=60 * 60).json()


@func_log
def sync_calculator_get_calculate_info():
    '''定时更新计算预览'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/calculator/get_calculate_info'
    return requests.post(url=url, data={'must_update_cache': '1'}, timeout=10 * 60).json()


@func_log
def sync_dashboard_overview():
    '''定时更新对照表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/dashboard/v2/get_overview'
    return requests.post(url=url, data={'must_update_cache': '1'}, timeout=10 * 60).json()


@func_log
def sync_dashboard_block_list():
    '''定时更新对照表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/dashboard/v2/get_block_list'
    return requests.post(url=url, data={'must_update_cache': '1'}, timeout=10 * 60).json()


@func_log
def sync_dashboard_miner_ranking():
    '''定时更新矿工排名'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/dashboard/v2/get_miner_ranking'
    return requests.post(url=url, data={'must_update_cache': '1'}, timeout=10 * 60).json()


@func_log
def sync_dashboard_power_distribution():
    '''定时更新对照表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/dashboard/v2/get_power_distribution'
    return requests.post(url=url, data={'must_update_cache': '1'}, timeout=10 * 60).json()


@func_log
def sync_dashboard_pool_overview():
    '''定时更新对照表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/dashboard/v2/get_pool_overview'
    return requests.post(url=url, data={'must_update_cache': '1'}, timeout=10 * 60).json()


@func_log
def sync_dashboard_day_pool_overview():
    '''定时更新对照表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/dashboard/v2/sync_day_pool_overview'
    return requests.post(url=url, data={'must_update_cache': '1'}, timeout=10 * 60).json()


@func_log
def sync_total_power_day_record():
    '''定时更新对照表'''
    url = os.getenv('SERVER_ACTIVITY') + '/activity/api/calculator/sync_total_power_day_record'
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    return requests.post(url=url, data={'date': yesterday_str}, timeout=10 * 60).json()


@func_log
def sync_explorer_pro_miner_monitor():
    '''浏览器PRO节点监控'''
    url = os.getenv('SERVER_EXPLORER') + '/explorer/api/pro/sync_update_miner_monitor'
    return requests.post(url=url, timeout=3600, data={}).json()


@func_log
def sync_explorer_pro_wallet_monitor():
    """浏览器PRO钱包流程监控监控"""
    url = os.getenv('SERVER_EXPLORER') + '/explorer/api/pro/sync_update_wallet_monitor'
    return requests.post(url=url, timeout=3600, data={}).json()


if __name__ == '__main__':
    logging.warning('定时任务开启...')
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    # scheduler.add_job(func=aps_test, args=('定时任务',), trigger='cron', second='*/5')
    # scheduler.add_job(func=aps_test, args=('一次性任务',), next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=12))
    # scheduler.add_job(func=aps_test, args=('循环任务',), trigger='interval', seconds=3)

    # scheduler.add_job(func=sync_overview, trigger='interval', seconds=40)
    # scheduler.add_job(func=sync_miner_ranking, trigger='interval', seconds=65)
    # scheduler.add_job(func=sync_miner_increase_ranking, trigger='interval', seconds=70)
    # scheduler.add_job(func=sync_block_ranking, trigger='interval', seconds=75)
    # scheduler.add_job(func=sync_balance_ranking, trigger='interval', seconds=80)
    # scheduler.add_job(func=sync_block_list, trigger='interval', seconds=85)
    # scheduler.add_job(func=sync_power_increase, trigger='interval', seconds=90)

    scheduler.add_job(func=sync_calculator_total_power_per_hour, trigger='cron', hour='*/1')
    scheduler.add_job(func=sync_calculator_tipset, trigger='cron', hour='8')
    scheduler.add_job(func=sync_calculator_temp_tipset, trigger='interval', minutes=10)
    scheduler.add_job(func=sync_calculator_lookups, trigger='interval', minutes=30)
    scheduler.add_job(func=sync_calculator_gas_fee, trigger='cron', hour='0', minute='1,3')
    scheduler.add_job(func=sync_calculator_get_calculate_info, trigger='cron', minute='*/2')
    scheduler.add_job(func=sync_total_power_day_record, trigger='cron', hour="6")

    scheduler.add_job(func=sync_dashboard_overview, trigger='interval', seconds=55)
    scheduler.add_job(func=sync_dashboard_block_list, trigger='interval', seconds=60)
    scheduler.add_job(func=sync_dashboard_miner_ranking, trigger='interval', minutes=18)
    scheduler.add_job(func=sync_dashboard_power_distribution, trigger='interval', minutes=60)
    scheduler.add_job(func=sync_dashboard_pool_overview, trigger='interval', minutes=10)
    scheduler.add_job(func=sync_dashboard_day_pool_overview, trigger='cron', hour="23", minute='59')

    scheduler.add_job(func=sync_explorer_pro_miner_monitor, trigger='interval', hours=2)
    scheduler.add_job(func=sync_explorer_pro_wallet_monitor, trigger='interval', hours=2)

    scheduler.start()
