import os

# 错误字典
ERROR_DICT = {
    0: 'ok',
    99901: '参数缺失',
    99902: '参数异常',
    99903: '参数重复',
    99904: '系统错误',
    99905: '请登录之后再操作',
    10001: 'Unsupported version of the interface',
    10002: '	Invalid appid',
    10400: 'Data verification failed, missing parameters, etc.',
    10403: 'The request was rejected, timed out, or SignatureNonce was repeated',
    20001: 'Signature verification failed',
    40000: 'Unknown business error',

}

# devcode
DEVCODE = os.getenv('DEVCODE', 'dev')

# 来源字典
SOURCE_H5 = 'h5bsdff'
SOURCE_ADMIN = 'admin'
SOURCE_RMD = 'rmdxxx'
SOURCE_FFM = 'famxxxxx'
SOURCE_CHAIN = 'chainbxxx'
SOURCE_GPU = 'gpuxxx'
SOURCE_LLQ = 'llqxxx'
SOURCE_ST = 'stsxxxxxx33335'
SOURCE_DICT = {
    SOURCE_H5: '网页', SOURCE_ADMIN: '管理后台', SOURCE_RMD: 'MINING POOL', SOURCE_FFM: 'fam',
    SOURCE_CHAIN: '链服务器', SOURCE_GPU: '云GPU小程序', SOURCE_LLQ: '浏览器小程序',
    SOURCE_ST: 'MTXSTORAGE'
}
# 付费用户
paying_user = [SOURCE_ADMIN]
# 免费用户
free_user = [SOURCE_H5]
# 主域名
MAIN_DOMAIN = "arockpool.com"

# 微服务地址
SERVER_ACCOUNT = os.getenv('SERVER_ACCOUNT')
SERVER_PROFILE = os.getenv('SERVER_PROFILE')
SERVER_SYSTEM = os.getenv('SERVER_SYSTEM')
SERVER_ACTIVITY = os.getenv('SERVER_ACTIVITY')
SERVER_POOL = os.getenv('SERVER_POOL')
SERVER_EXPLORER = os.getenv('SERVER_EXPLORER')
# SERVER_DATA = "http://testapi-explorer.arockpool.com"
SERVER_DATA = os.getenv('SERVER_DATA')
SERVER_GPU = os.getenv('SERVER_GPU')
BBHEMNG_HOST = os.getenv('BBHEMNG_HOST')
SERVER_EXPLORER_V2 = os.getenv('SERVER_EXPLORER_V2')


# 图片服务域名
IMG_DOMAIN = "https://%s.%s" % (OSS_BUCKET_NAME, OSS_ENDPOINT)

# 邮件配置
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_SENDER_NICK = os.getenv('EMAIL_SENDER_NICK')
EMAIL_SENDER_PASSWORD = os.getenv('EMAIL_SENDER_PASSWORD')
EMAIL_NOTICE_GROUP = os.getenv('EMAIL_NOTICE_GROUP')

# BBHE配置
BBHEHOST = os.getenv('BBHEHOST')
BBHESECRET = os.getenv('BBHESECRET')
BBHEES_HOST = os.getenv('BBHEES_HOST')
BBHEES_USER = os.getenv('BBHEES_USER')
BBHEES_PASSWORD = os.getenv('BBHEES_PASSWORD')

# FAM配置
FAM_HOST = os.getenv('FAM_HOST')
FAM_APP_ID = os.getenv('FAM_APP_ID')
FAM_APP_SECRET = os.getenv('FAM_APP_SECRET')

# MINING POOL整体统计
STATISTICS_HOST = os.getenv('STATISTICS_HOST')

# 签名验证
BBHEFILLOTUS_HOST = os.getenv('BBHEFILLOTUS_HOST')
