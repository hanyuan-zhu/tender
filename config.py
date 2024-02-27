# 配置信息
CHROMEDRIVER_PATH = '/opt/homebrew/bin/chromedriver'
HEADLESS = True
WEBPAGE_URL = "http://deal.ggzy.gov.cn/ds/deal/dealList.jsp?HEADER_DEAL_TYPE=01"
# DB_CONFIG = {
#     'host': 'gz-cdb-5scrcjb5.sql.tencentcdb.com',
#     'user': 'db',
#     'password': 'dbdb905905',
#     'database': 'sele',
#     'port': 63432,
#     'charset': 'utf8mb4'
# }

DB_CONFIG = {
    'host': 'localhost',  # 数据库服务器地址
    'port': 3306,  # 数据库服务器端口号
    'user': 'root',  # 数据库用户名
    'password': '',  # 数据库密码
    'db': 'tenders',  # 数据库名
    'charset': 'utf8mb4',  # 数据库字符集
}

# 数据表名
TENDER_INFO_TABLE_NAME = 'tender_info'
# TENDER_INFO_TABLE_NAME = 'tender_index'
TENDER_DETAIL_TABLE_NAME = 'tender_detail_html'
