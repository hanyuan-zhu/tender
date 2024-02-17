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

def check_existence(cursor, link):
    cursor.execute("SELECT COUNT(*) FROM tender_info WHERE detail_link = %s", (link,))
    return cursor.fetchone()[0] > 0

def insert_data(cursor, data):
    insert_query = """INSERT INTO tender_info (title, publish_time, province, source_platform, business_type, info_type, industry, detail_link)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(insert_query, data)
