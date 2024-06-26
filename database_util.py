import mysql.connector
from mysql.connector import Error
import datetime
from config import DB_CONFIG, TENDER_INDEX_TABLE_NAME, TENDER_DETAIL_HTML_TABLE_NAME,TENDER_DETAIL_TABLE_NAME
import logging

def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

############################################################################################################
# 以下函数用于crawlIndex.py：
# - check_existence
# - insert_data
############################################################################################################
def check_existence(cursor, link):
    cursor.execute(f"SELECT COUNT(*) FROM {TENDER_INDEX_TABLE_NAME} WHERE detail_link = %s", (link,))
    return cursor.fetchone()[0] > 0

def insert_data(cursor, data):
    insert_query = f"""INSERT INTO {TENDER_INDEX_TABLE_NAME} (title, publish_time, province, source_platform, business_type, info_type, industry, detail_link)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(insert_query, data)

############################################################################################################
# 以下函数用于crawlDetail.py：
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
    FROM {TENDER_INDEX_TABLE_NAME} 
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
    UPDATE {TENDER_INDEX_TABLE_NAME}
    SET detail_info_fetched = TRUE
    WHERE id = %s
    """
    cursor.execute(update_query, (tender_id,))

############################################################################################################
# 以下函数用于cleanHtml.py：
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
# 以下函数用于aiExtract.py：
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
    # SELECT t.tender_id, t.cleaned_detail_html
    # FROM {TENDER_DETAIL_HTML_TABLE_NAME} t
    # JOIN announcement_labels al ON t.tender_id = al.tender_id
    # WHERE (t.last_extracted_time IS NULL OR t.last_extracted_time < DATE_SUB(NOW(), INTERVAL 1 DAY))
    # AND al.type_id IN (1, 2)
    # """
    select_query = f"""
    SELECT t.tender_id, t.cleaned_detail_html
    FROM {TENDER_DETAIL_HTML_TABLE_NAME} t
    JOIN announcement_labels al ON t.tender_id = al.tender_id
    WHERE t.last_extracted_time IS NULL
    AND al.type_id IN (1, 2)
    """
    cursor.execute(select_query)
    return cursor.fetchall()

def insert_data_into_tender_detail(data):
    """
    将数据插入到tender_detail表中。

    参数:
    data -- 一个字典，包含要插入的字段名和对应的值。例如：{'field1': 'value1', 'field2': 'value2'}

    返回值:
    无

    使用方法:
    1. 准备一个包含要插入的字段名和对应的值的字典。
    2. 调用此函数，传入字典，将数据插入到tender_detail表中。

    注意:
    此函数不会检查字段名是否存在于表中，如果字段名不存在，将会导致错误。请在调用此函数前确保字段名是正确的。
    此函数也不会检查是否有重复的记录，如果插入的数据已存在于表中，可能会导致错误。请在调用此函数前确保数据在表中是唯一的。
    """

    
    with connect_db() as db:
        if db is None:
            print("Failed to connect to the database.")
            return
        if data is None:
            print("Error: data is None.")
            return

        fields = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        insert_query = f"INSERT INTO {TENDER_DETAIL_TABLE_NAME} ({fields}) VALUES ({values})"

        with db.cursor() as cursor:
            cursor.execute(insert_query, list(data.values()))
            db.commit()

        print("Data inserted into tender_detail successfully.")

def update_last_extracted_time(db,cursor, tender_id):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    update_sql = f"UPDATE {TENDER_DETAIL_HTML_TABLE_NAME} SET last_extracted_time = %s WHERE tender_id = %s"
    cursor.execute(update_sql, (now, tender_id))
    db.commit()
    logging.info(f"更新 tender_id 为 {tender_id} 的最后提取时间")
    
############################################################################################################
# 以下函数用于tenderLabeling.py：
# - get_tender_title
# - get_announcement_types
# - insert_into_announcement_labels
############################################################################################################
    

def get_tender_title(cursor):
    """
    从数据库中获取所有未被标记的招标标题。
    返回值:
    一个元组列表，每个元组包含两个元素：招标信息的ID和标题。
    """

    select_query = f"""
    SELECT id, title
    FROM {TENDER_INDEX_TABLE_NAME}
    WHERE id NOT IN (
        SELECT tender_id
        FROM announcement_labels
    )
    """
    cursor.execute(select_query)
    return cursor.fetchall()

def get_announcement_types(cursor):
    """
    从数据库中获取所有的公告类型。
    返回值:
    一个字典，键是公告类型，值是对应的ID。
    """

    select_query = "SELECT id, announcement_type FROM announcement_catalog"
    cursor.execute(select_query)
    results = cursor.fetchall()
    return {type: id for id, type in results}

def insert_into_announcement_labels(cursor, tender_id, type_id):
    """
    将招标信息的类型插入到数据库中。
    参数:
    cursor -- 数据库游标
    tender_id -- 招标信息的ID
    type_id -- 公告类型的ID
    """

    insert_query = f"INSERT INTO announcement_labels (tender_id, type_id) VALUES ({tender_id}, {type_id})"
    cursor.execute(insert_query)    


############################################################################################################
# 以下函数用于aiKeyElementExtract.py：
# get_all_cleaned_htmls_to_extract_key
# insert_data_into_db
############################################################################################################

def get_all_cleaned_htmls_to_extract_key(cursor):
    # 获取已经处理过的tender_id
    cursor.execute("SELECT tender_id FROM raw_tender_key_detail")
    existing_tender_ids = [row[0] for row in cursor.fetchall()]
    # 创建一个字符串，其中包含与元组中的元素数量相同的占位符
    placeholders = ', '.join(['%s'] * len(existing_tender_ids))
    # 查询满足特定条件且不在这两个表中的tender_id
    query = f"""
        SELECT t.tender_id, t.cleaned_detail_html
        FROM {TENDER_DETAIL_HTML_TABLE_NAME} t
        JOIN announcement_labels al ON t.tender_id = al.tender_id
        WHERE al.type_id IN (1, 2) AND t.tender_id NOT IN ({placeholders})
        ORDER BY t.tender_id DESC
    """
    cursor.execute(query, tuple(existing_tender_ids))
    result = cursor.fetchall()
    return result


def insert_data_into_db(db, cursor, raw_data, processed_data):
    """Insert processed data into the database using the provided cursor. Handle reconnection if necessary."""
    try:
        insert_into_raw_tender_key_detail(cursor, raw_data)
        insert_into_tender_key_detail(cursor, processed_data)
        db.commit()
    except Exception as e:
        logging.error(f"Database insert failed: {e}")
        # Attempt to reconnect
        db = connect_db()
        if db is not None:
            new_cursor = db.cursor()
            logging.debug("Database reconnected, returning new db and cursor.")
            return (db, new_cursor)
        else:
            logging.debug("Reconnection failed, returning None, None.")
            return (None, None)
    logging.debug("Data inserted successfully, returning db and cursor.")
    return (db, cursor)

        
def insert_into_raw_tender_key_detail(cursor,raw_tender_dict):
    raw_tender_dict = remove_invalid_keys(cursor, raw_tender_dict, "raw_tender_key_detail")
    keys = ', '.join(raw_tender_dict.keys())
    values = ', '.join(['%s'] * len(raw_tender_dict))
    sql = f"INSERT INTO raw_tender_key_detail ({keys}) VALUES ({values})"
    cursor.execute(sql, list(raw_tender_dict.values()))

def insert_into_tender_key_detail(cursor,post_processed_dict):
    post_processed_dict = remove_invalid_keys(cursor, post_processed_dict, "tender_key_detail")
    keys = ', '.join(post_processed_dict.keys())
    values = ', '.join(['%s'] * len(post_processed_dict))
    sql = f"INSERT INTO tender_key_detail ({keys}) VALUES ({values})"
    cursor.execute(sql, list(post_processed_dict.values()))
    
def get_column_names(cursor, table_name):
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    return [column[0] for column in cursor.fetchall()]

def remove_invalid_keys(cursor, data_dict, table_name):
    column_names = get_column_names(cursor, table_name)
    return {key: value for key, value in data_dict.items() if key in column_names}
