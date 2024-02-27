import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG, TENDER_INFO_TABLE_NAME, TENDER_DETAIL_TABLE_NAME

def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

import config

def check_existence(cursor, link):
    cursor.execute(f"SELECT COUNT(*) FROM {TENDER_INFO_TABLE_NAME} WHERE detail_link = %s", (link,))
    return cursor.fetchone()[0] > 0

def insert_data(cursor, data):
    insert_query = f"""INSERT INTO {TENDER_INFO_TABLE_NAME} (title, publish_time, province, source_platform, business_type, info_type, industry, detail_link)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(insert_query, data)


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

def insert_detail_data(cursor, data):
    """
    将爬取到的详细信息插入到数据库中。
    参数:
    - cursor: 数据库游标。
    - data: 要插入的数据，预期为一个元组，包含(tender_id, title, publish_time, original_link, original_detail_html)。
    """
    insert_query = f"""
    INSERT INTO {TENDER_DETAIL_TABLE_NAME} (tender_id, title, publish_time, original_link, original_detail_html)
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
    FROM {TENDER_DETAIL_TABLE_NAME} 
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
    UPDATE {TENDER_DETAIL_TABLE_NAME}
    SET cleaned_detail_html = %s
    WHERE id = %s
    """
    cursor.execute(update_query, (cleaned_html, id))