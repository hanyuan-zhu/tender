import mysql.connector
from mysql.connector import Error
import datetime
from config import DB_CONFIG, TENDER_INFO_TABLE_NAME, TENDER_DETAIL_HTML_TABLE_NAME

def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

############################################################################################################
# 以下函数用于crawl_index.py：
# - check_existence
# - insert_data
############################################################################################################
def check_existence(cursor, link):
    cursor.execute(f"SELECT COUNT(*) FROM {TENDER_INFO_TABLE_NAME} WHERE detail_link = %s", (link,))
    return cursor.fetchone()[0] > 0

def insert_data(cursor, data):
    insert_query = f"""INSERT INTO {TENDER_INFO_TABLE_NAME} (title, publish_time, province, source_platform, business_type, info_type, industry, detail_link)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(insert_query, data)

############################################################################################################
# 以下函数用于crawl_detail.py：
# - get_unfetched_tender_info
# - insert_detail_html
# - update_fetched_status
############################################################################################################
def get_unfetched_tender_info(cursor):
    """
    从数据库中获取所有未抓取的招标信息。

    参数:
    cursor -- 数据库游标

    返回值:
    一个包含所有未抓取的招标信息的元组，每个信息是一个包含id和detail_link的元组。
    """
    select_query = f"""
    SELECT id, detail_link 
    FROM {TENDER_INFO_TABLE_NAME} 
    WHERE detail_info_fetched = FALSE
    """
    cursor.execute(select_query)
    return cursor.fetchall()

def insert_detail_html(cursor, data):
    """
    将爬取到的详细信息插入到数据库中。
    参数:
    - cursor: 数据库游标。
    - data: 要插入的数据，预期为一个元组，包含(tender_id, title, publish_time, original_link, original_detail_html)。
    """
    insert_query = f"""
    INSERT INTO {TENDER_DETAIL_HTML_TABLE_NAME} (tender_id, title, publish_time, original_link, original_detail_html)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, data)

def update_fetched_status(cursor, tender_id):
    update_query = f"""
    UPDATE {TENDER_INFO_TABLE_NAME}
    SET detail_info_fetched = TRUE
    WHERE id = %s
    """
    cursor.execute(update_query, (tender_id,))

############################################################################################################
# 以下函数用于clean_html.py：
# - get_uncleaned_html_records
# - update_cleaned_html
############################################################################################################
def get_uncleaned_html_records(cursor):
    """
    从数据库中获取所有未清洗的HTML记录。

    参数:
    cursor -- 数据库游标

    返回值:
    一个包含所有未清洗的HTML记录的元组，每个记录是一个包含id和original_detail_html的元组。
    """
    select_query = f"""
    SELECT id, original_detail_html 
    FROM {TENDER_DETAIL_HTML_TABLE_NAME} 
    WHERE cleaned_detail_html IS NULL AND original_detail_html IS NOT NULL
    """
    cursor.execute(select_query)
    return cursor.fetchall()

def update_cleaned_html(cursor, cleaned_html, id):
    """
    更新数据库中的清洗后的HTML。

    参数:
    cursor -- 数据库游标
    cleaned_html -- 清洗后的HTML
    id -- 要更新的记录的id
    """
    update_query = f"""
    UPDATE {TENDER_DETAIL_HTML_TABLE_NAME}
    SET cleaned_detail_html = %s
    WHERE id = %s
    """
    cursor.execute(update_query, (cleaned_html, id))

############################################################################################################
# 以下函数用于ai_extract.py：
# - get_all_cleaned_htmls_to_extract
# - insert_data_into_tender_detail
# - update_last_extracted_time
############################################################################################################
def get_all_cleaned_htmls_to_extract(cursor):
    """
    获取所有未提取或需要重新提取信息的cleaned_html条目。
    
    参数:
    cursor -- 数据库游标

    返回值:
    一个包含待提取条目的tender_id和cleaned_html的列表。
    """
    # 注意替换这里的YOUR_CONDITION_WITH_SPECIFIC_TIME为具体的条件
    # 例如，你可以设置为 "last_extracted_time IS NULL OR last_extracted_time < DATE_SUB(NOW(), INTERVAL 1 DAY)"
    # 来获取所有没有提取过，或者最后提取时间早于当前时间24小时的记录
    # select_query = f"""
    # SELECT tender_id, cleaned_detail_html
    # FROM {TENDER_DETAIL_HTML_TABLE_NAME}
    # WHERE last_extracted_time IS NULL OR last_extracted_time < YOUR_CONDITION_WITH_SPECIFIC_TIME
    # """
    select_query = f"""
    SELECT tender_id, cleaned_detail_html
    FROM {TENDER_DETAIL_HTML_TABLE_NAME}
    WHERE last_extracted_time IS NULL
    """
    cursor.execute(select_query)
    return cursor.fetchall()

def insert_data_into_tender_detail(data):
    with connect_db() as db:
        if db is None:
            print("Failed to connect to the database.")
            return
        if data is None:
            print("Error: data is None.")
            return

        fields = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        insert_query = f"INSERT INTO tender_detail ({fields}) VALUES ({values})"

        with db.cursor() as cursor:
            cursor.execute(insert_query, list(data.values()))
            db.commit()

        print("Data inserted into tender_detail successfully.")

def update_last_extracted_time(db,cursor, tender_id):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    update_sql = "UPDATE tender_detail_html SET last_extracted_time = %s WHERE tender_id = %s"
    cursor.execute(update_sql, (now, tender_id))
    db.commit()

# def insert_detail_data(data):
#     """
#     将招标详细信息插入到数据库中。
#     参数:
#     - data: 要插入的数据，预期为一个元组，包含所有必要的招标详细信息字段。
#     """
#     connection = connect_db()
#     if connection is not None:
#         try:
#             cursor = connection.cursor()
#             insert_query = f"""
#             INSERT INTO {TENDER_DETAIL_HTML_TABLE_NAME} (tender_id, tender_document_start_time, tender_document_end_time, question_deadline, answer_announcement_time, bid_submission_deadline, bid_opening_time, tenderer, tender_contact, contact_phone, tender_agency, tender_agency_contact, tender_agency_contact_phone, supervision_qualification_requirement, business_license_requirement, chief_supervisor_qualification_requirement, consortium_bidding_requirement, project_name, investment_project_code, tender_project_name, implementation_site, funding_source, tender_scope_and_scale, duration, maximum_bid_price, qualification_review_method)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#             """
#             cursor.execute(insert_query, data)
#             connection.commit()
#         except Error as e:
#             print(f"Error: {e}")
#             connection.rollback()
#         finally:
#             cursor.close()
#             connection.close()
