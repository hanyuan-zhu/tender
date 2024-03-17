# 配置信息
# CHROMEDRIVER_PATH = '/opt/homebrew/bin/chromedriver'
CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver' #  这个是sele服务器的chromedriver地址
# 记得一定要配置当前环境 chromedriver 的路径，用 "which chromedriver"找到

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

## 用于本地测试的配置
# DB_CONFIG = {
#     'host': 'localhost',  # 数据库服务器地址
#     'port': 3306,  # 数据库服务器端口号
#     'user': 'root',  # 数据库用户名
#     'password': '',  # 数据库密码
#     'db': 'tenders',  # 数据库名
#     'charset': 'utf8mb4',  # 数据库字符集
# }

# 数据表名
# 招标列表信息表，
## 包含“招标标题、发布时间、省份、来源平台、业务类型、信息类型、行业、详情链接、是否已抓取详情信息”
TENDER_INFO_TABLE_NAME = 'tender_index'
# 对应的数据库表结构如下：
# +---------------------+--------------+------+-----+---------+----------------+
# | Field               | Type         | Null | Key | Default | Extra          |
# +---------------------+--------------+------+-----+---------+----------------+
# | id                  | int(11)      | NO   | PRI | NULL    | auto_increment | # 主键，自动增长
# | title               | varchar(255) | YES  |     | NULL    |                | # 招标标题
# | publish_time        | date         | YES  |     | NULL    |                | # 发布时间
# | province            | varchar(100) | YES  |     | NULL    |                | # 省份
# | source_platform     | varchar(100) | YES  |     | NULL    |                | # 来源平台
# | info_type           | varchar(100) | YES  |     | NULL    |                | # 信息类型
# | business_type       | varchar(100) | YES  |     | NULL    |                | # 业务类型
# | industry            | varchar(100) | YES  |     | NULL    |                | # 行业
# | detail_link         | varchar(255) | YES  |     | NULL    |                | # 详情链接
# | detail_info_fetched | tinyint(1)   | YES  |     | 0       |                | # 是否已抓取详情信息，0表示未抓取，1表示已抓取
# +---------------------+--------------+------+-----+---------+----------------+


# 招标详情信息(原始HTML）表，
## 包含“招标ID、招标标题、发布时间、原文链接、原始HTML内容、已清洗HTML内容、最后提取时间”
TENDER_DETAIL_HTML_TABLE_NAME = 'tender_detail_html'
# 对应的数据库表结构如下：
# +----------------------+--------------+------+-----+---------+----------------+
# | Field                | Type         | Null | Key | Default | Extra          |
# +----------------------+--------------+------+-----+---------+----------------+
# | id                   | int(11)      | NO   | PRI | NULL    | auto_increment | # 主键，自动增长
# | tender_id            | int(11)      | NO   | MUL | NULL    |                | # 招标ID
# | title                | varchar(255) | YES  |     | NULL    |                | # 招标标题
# | publish_time         | datetime     | YES  |     | NULL    |                | # 发布时间
# | original_link        | varchar(255) | YES  |     | NULL    |                | # 原文链接
# | original_detail_html | mediumtext   | YES  |     | NULL    |                | # 原始HTML内容
# | cleaned_detail_html  | mediumtext   | YES  |     | NULL    |                | # 已清洗HTML内容
# | last_extracted_time  | datetime     | YES  |     | NULL    |                | # 最后提取时间
# +----------------------+--------------+------+-----+---------+----------------+

# 招标详情信息表 
# 结构化提取后的招标详情信息表，
TENDER_DETAIL_TABLE_NAME = 'tender_detail'
# TENDER_DETAIL_TABLE_NAME = 'tender_detail_temp' ## backup_plan 用的测试表

# 公告类型目录表，
## 包含“公告类型”
ANNOUNCEMENT_CATALOG_TABLE_NAME = 'announcement_catalog'
# 对应的数据库表结构如下：
# +-------------------+--------------+------+-----+---------+----------------+
# | Field             | Type         | Null | Key | Default | Extra          |
# +-------------------+--------------+------+-----+---------+----------------+
# | id                | int(11)      | NO   | PRI | NULL    | auto_increment | # 主键，自动增长
# | announcement_type | varchar(255) | YES  |     | NULL    |                | # 公告类型
# +-------------------+--------------+------+-----+---------+----------------+


# 公告类型标注表，
## 对应 tender_id 和 announcement_type_id 的关系
ANNOUNCEMENT_LABELS_TABLE_NAME = 'announcement_labels'
# 对应的数据库表结构如下：
# +-----------+---------+------+-----+---------+----------------+
# | Field     | Type    | Null | Key | Default | Extra          |
# +-----------+---------+------+-----+---------+----------------+
# | id        | int(11) | NO   | PRI | NULL    | auto_increment | # 主键，自动增长
# | tender_id | int(11) | YES  | MUL | NULL    |                | # 招标ID
# | type_id   | int(11) | YES  | MUL | NULL    |                | # 公告类型ID
# +-----------+---------+------+-----+---------+----------------+