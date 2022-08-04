import os
import datetime
import logging
import requests
import threading
from functools import wraps
from apscheduler.schedulers.blocking import BlockingScheduler
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(BASE_DIR))

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
def sync_miner_info():
    '''
    同步矿工信息
    '''
    url = os.getenv('SERVER_POOL') + '/pool/admin/miner/sync_miner_info'
    return requests.post(url=url, timeout=300).json()


@func_log
def sync_cluster_info():
    '''
    同步集群信息
    '''
    url = os.getenv('SERVER_POOL') + '/pool/admin/cluster/sync_cluster_info'
    return requests.post(url=url, timeout=30).json()


@func_log
def sync_company_store():
    '''
    瓜分算力
    '''
    url = os.getenv('SERVER_POOL') + '/pool/admin/machine/sync_company_store'
    return requests.post(url=url, timeout=30).json()


@func_log
def sync_company_info():
    '''
    同步机构信息
    '''
    url = os.getenv('SERVER_POOL') + '/pool/admin/company/sync_company_info'
    return requests.post(url=url, timeout=30).json()


@func_log
def sync_miner_block_list():
    '''
    同步矿工区块
    '''
    url = os.getenv('SERVER_POOL') + '/pool/admin/miner/sync_miner_block_list'
    return requests.post(url=url, timeout=300).json()


def sync_data():
    sync_miner_info()
    sync_cluster_info()
    sync_company_store()
    sync_company_info()
    sync_miner_block_list()


@func_log
def sync_delete_cache():
    '''
    释放质押
    '''
    url = os.getenv('SERVER_POOL') + '/pool/admin/company/sync_delete_cache'
    return requests.post(url=url, timeout=300).json()


# 同步链上用户钱包信息
def sync_pledge_recharge_record(data={}):
    """
    同步用户worker充值记录
    """
    url = '%s/pool/admin/wallet/sync_pledge_recharge_record' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, timeout=300, data=data).json()


def sync_gas_recharge_record(data={}):
    """
    同步用户可用充值记录
    """
    url = '%s/pool/admin/wallet/sync_gas_recharge_record' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, data=data, timeout=300).json()


def sync_set_cost_earnings(data={}):
    """
    获得今日挖矿效率,gas费,扇区质押
    """
    url = '%s/pool/admin/company/sync_set_cost_earnings' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, data=data, timeout=300).json()


def sync_earnings_online_miner(data={}):
    """
    计算今日链上用户收益
    """
    url = '%s/pool/admin/company/v2/sync_earnings_circulation' % (os.getenv('SERVER_POOL'))
    result = requests.post(url=url, data=data, timeout=1800)
    print(result)
    return result.json()


def sync_worker_online_miner_cost(data={}):
    """
    获得今日链上用户worker钱包消费情况
    """
    url = '%s/pool/admin/company/v2/sync_sectors_worker_circulation' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, data=data, timeout=1800).json()


def sync_gas_online_miner_cost(data={}):
    """
    获得今日链上用户post钱包发出情况
    """
    url = '%s/pool/admin/company/v2/sync_post_circulation' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, timeout=1800, data=data).json()


@func_log
def sync_recharge_record():
    """
    同步链上矿工的充值记录
    :return:
    """
    result = sync_gas_recharge_record()
    # print(result)
    result = sync_pledge_recharge_record()
    # print(result)


@func_log
def sync_carve_online_miner(data={}):
    """
    同步链上用户当日的收益,费用情况
    """
    result = sync_earnings_online_miner(data)  # 收益
    # print(result)
    # result = sync_worker_online_miner_cost(data)  # 扇区质押
    # print(result)
    # result = sync_gas_online_miner_cost(data)  # gas费
    # print(result)


@func_log
def sync_carve_wallet_cost(data={}):
    """
    同步链上用户当日的收益,费用情况
    """
    result = sync_worker_online_miner_cost(data)  # worker
    print(result)
    result = sync_gas_online_miner_cost(data)  # post
    print(result)


@func_log
def sync_power_online(data={}):
    """
    同步链上矿工每日的算力,需要在每天的0时执行
    :return:
    """
    url = '%s/pool/admin/company/v2/sync_power_online' % (os.getenv('SERVER_POOL'))
    result = requests.post(url=url, timeout=300, data=data).json()
    print(result)
    return result


@func_log
def release_pledge(data={}):
    """
    释放质押
    """
    url = '%s/pool/admin/company/sync_release_pledge_coin' % (os.getenv('SERVER_POOL'))
    result = requests.post(url=url, timeout=300, data=data).json()
    # print(result)
    return result


@func_log
def estimated_sector_pledge_amount():
    url = os.getenv('SERVER_POOL') + '/pool/admin/machine/server/estimated_sector_pledge_amount'
    response = requests.post(url=url, data={'flag': 'timing'})
    return response.content.decode()


@func_log
def sync_carve_by_unite_miner(data={}):
    """
    联合挖矿收益分配
    """
    url = '%s/pool/admin/company/sync_carve_by_unite_miner' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sync_carve_by_plus_order(data={}):
    """
    MTXSTORAGE订单收益分配
    """
    url = '%s/pool/admin/company/sync_carve_by_plus_order' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sync_carve_by_B_port(data={}):
    """
    372订单收益分配
    """
    url = '%s/pool/admin/company/sync_carve_by_B_port' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sync_deal_info(data={}):
    """
    MTXSTORAGE更新未写入数据的deal详情
    """
    url = '%s/pool/admin/dealorder/sync_deal_info' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sms_remind_72(data={"hour": 72}):
    """
    短信提醒 24-48小时的
    """
    if os.getenv('DEVCODE', 'prod'):
        url = '%s/pool/admin/wallet/task/sms_remind' % (os.getenv('SERVER_POOL'))
        return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sms_remind_24(data={"hour": 24}):
    """
    短信提醒 0-24小时的
    """
    if os.getenv('DEVCODE', 'prod'):
        url = '%s/pool/admin/wallet/task/sms_remind' % (os.getenv('SERVER_POOL'))
        return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sync_create_bill(data={}):
    """
    创建账单
    """
    if os.getenv('DEVCODE', 'prod'):
        url = '%s/pool/admin/bill/sync_create_bill' % (os.getenv('SERVER_POOL'))
        return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sync_secret_to_cache(data={}):
    """
    写入app_id和私钥到redis
    """
    if os.getenv('DEVCODE', 'prod'):
        url = '%s/pool/admin/output/sync_secret_to_cache' % (os.getenv('SERVER_POOL'))
        return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sms_remind_withdraw_deposit(data={}):
    """
    短信提醒
    """
    if os.getenv('DEVCODE') in ['prod', 'test']:
        url = '%s/pool/admin/wallet/task/sms_remind_withdraw_deposit' % (os.getenv('SERVER_POOL'))
        return requests.post(url=url, timeout=300, data=data).json()


@func_log
def sync_detection_release_pledge(data={}):
    url = '%s/pool/admin/company/sync_detection_release_pledge' % (os.getenv('SERVER_POOL'))
    return requests.post(url=url, timeout=300, data=data).json()


if __name__ == '__main__':
    logging.warning('定时任务开启...')
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    # scheduler.add_job(func=aps_test, args=('定时任务',), trigger='cron', second='*/5')
    # scheduler.add_job(func=aps_test, args=('一次性任务',), next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=12))
    # scheduler.add_job(func=aps_test, args=('循环任务',), trigger='interval', seconds=3)
    # scheduler.add_job(func=sync_data, trigger='cron', hour=0, minute=10)
    # scheduler.add_job(func=sync_miner_block_list, trigger='interval', minutes=10)
    # scheduler.add_job(func=sync_machine_list, trigger='interval', seconds=60 * 60)  # 同步矿池中昨日新增的的矿机
    # scheduler.add_job(func=sync_machine_yesterday_error_time, trigger='interval', seconds=60 * 60)  # 同步矿池中的矿机昨日异常的小时数
    # scheduler.add_job(func=sync_machine_message, trigger='interval', seconds=60 * 60)  # 同步矿机数据
    # scheduler.add_job(func=allocation_power, trigger='cron', hour=12, minute=10)  # 分配算力
    scheduler.add_job(func=estimated_sector_pledge_amount, trigger='interval', seconds=60 * 60)  # 获得扇区预估质押
    # scheduler.add_job(func=sync_recharge_record, trigger='interval', seconds=15 * 60)  # 同步充值记录
    # scheduler.add_job(func=sync_carve_online_miner, trigger='interval', seconds=60 * 15)  # 链上矿工收益同步
    # scheduler.add_job(func=sync_carve_wallet_cost, trigger='cron', hour=2, minute=50)  # 计算worker,post钱包前一日消耗 直接从es读,不保存

    # scheduler.add_job(func=release_pledge, trigger='cron', hour=10, minute=50)  # 释放质押
    # scheduler.add_job(func=sync_carve_by_unite_miner, trigger='cron', hour=9, minute=30)  # 联合挖矿收益分配
    # scheduler.add_job(func=sync_carve_by_plus_order, trigger='cron', hour=8, minute=30)  # MTXSTORAGE订单收益分配定时任务
    # scheduler.add_job(func=sync_carve_by_B_port, trigger='cron', hour=10, minute=10)  # 372订单收益分配
    # scheduler.add_job(func=sync_deal_info, trigger='cron', hour=11, minute=10)  # MTXSTORAGE订单收益分配定时任务
    # scheduler.add_job(func=sync_power_online, trigger='cron', hour=9,
    #                   minute=10)  # 同步自质押订单前一日的累计算力,算力增量(自质押算力直接从接口获取,本地不再保存)
    # scheduler.add_job(func=sms_remind_72, trigger='interval', seconds=60 * 60 * 12)  # 短信余额不足提醒 24-72
    # scheduler.add_job(func=sms_remind_24, trigger='interval', seconds=60 * 60 * 6)  # 短信余额不足提醒 0-24
    # scheduler.add_job(func=sms_remind_withdraw_deposit, trigger='cron', hour=16, minute=58)  # 提现审核提醒
    # scheduler.add_job(func=sync_detection_release_pledge, trigger='cron', hour=11, minute=30)  # 检查线性释放
    # scheduler.add_job(func=sync_create_bill, trigger='cron', day=2)  # 创建一级订单的账单 每月5号执行
    scheduler.add_job(func=sync_secret_to_cache, trigger='interval', hours=2)  # 写入第三方用户的认证app_id,私钥
    scheduler.add_job(func=sync_secret_to_cache, trigger='date')  # 立即执行一次写入私钥
    scheduler.start()
