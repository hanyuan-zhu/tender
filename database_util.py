import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

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
    cursor.execute(f"SELECT COUNT(*) FROM {config.TENDER_INFO_TABLE_NAME} WHERE detail_link = %s", (link,))
    return cursor.fetchone()[0] > 0

def insert_data(cursor, data):
    insert_query = f"""INSERT INTO {config.TENDER_INFO_TABLE_NAME} (title, publish_time, province, source_platform, business_type, info_type, industry, detail_link)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(insert_query, data)

def insert_detail_data(cursor, data):
    """
    将爬取到的详细信息插入到数据库中。
    参数:
    - cursor: 数据库游标。
    - data: 要插入的数据，预期为一个元组，包含(tender_id, title, publish_time, original_link, original_detail_html)。
    """
    insert_query = f"""
    INSERT INTO {config.TENDER_DETAIL_TABLE_NAME} (tender_id, title, publish_time, original_link, original_detail_html)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, data)


def update_fetched_status(cursor, tender_id):
    update_query = f"""
    UPDATE {config.TENDER_INFO_TABLE_NAME}
    SET detail_info_fetched = TRUE
    WHERE id = %s
    """
    cursor.execute(update_query, (tender_id,))
