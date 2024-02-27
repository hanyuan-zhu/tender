# 配置信息
CHROMEDRIVER_PATH = '/opt/homebrew/bin/chromedriver'
HEADLESS = True
WEBPAGE_URL = "http://deal.ggzy.gov.cn/ds/deal/dealList.jsp?HEADER_DEAL_TYPE=01"
DB_CONFIG = {
    'host': 'gz-cdb-5scrcjb5.sql.tencentcdb.com',
    'user': 'db',
    'password': 'dbdb905905',
    'database': 'sele',
    'port': 63432,
    'charset': 'utf8mb4'
}

# DB_CONFIG = {
#     'host': 'localhost',  # 数据库服务器地址
#     'port': 3306,  # 数据库服务器端口号
#     'user': 'root',  # 数据库用户名
#     'password': '',  # 数据库密码
#     'db': 'tenders',  # 数据库名
#     'charset': 'utf8mb4',  # 数据库字符集
# }

# 数据表名

# 招标列表信息表，包含“招标标题、发布时间、省份、来源平台、业务类型、信息类型、行业、详情链接、是否已抓取详情信息”
TENDER_INFO_TABLE_NAME = 'tender_index'

# 招标详情信息表，包含“招标ID、招标标题、发布时间、原文链接、原始HTML内容、已清洗HTML内容”
TENDER_DETAIL_TABLE_NAME = 'tender_detail_html'
