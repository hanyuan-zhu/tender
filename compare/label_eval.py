# Description: 生成一个包含超链接的HTML表格，主要是来展示ai处理公告类型后的数据

from flask import Flask, render_template_string
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG  # 确保你的数据库配置在这个模块里

app = Flask(__name__)

# 连接数据库
def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

# 生成HTML的函数
def generate_html(cursor):
    query = """
    SELECT al.tender_id, ti.title, al.type_id, ac.announcement_type, ti.detail_link
    FROM announcement_labels al 
    JOIN tender_index ti ON al.tender_id = ti.id 
    JOIN announcement_catalog ac ON al.type_id = ac.id
    """
    cursor.execute(query)
    data = cursor.fetchall()

    # 生成HTML字符串
    html_content = "<table border='1'>\n"
    html_content += "<tr><th>Tender ID</th><th>Title</th><th>Type ID</th><th>Announcement Type</th></tr>\n"
    for row in data:
        # 在这里修改，将标题包装成一个超链接
        title_with_link = f"<a href='{row[4]}' target='_blank'>{row[1]}</a>"
        html_content += f"<tr><td>{row[0]}</td><td>{title_with_link}</td><td>{row[2]}</td><td>{row[3]}</td></tr>\n"
    html_content += "</table>"
    return html_content

@app.route('/')
def index():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        html_content = generate_html(cursor)
        cursor.close()
        conn.close()
    else:
        html_content = "<p>Error connecting to database.</p>"
    # 使用render_template_string渲染HTML
    return render_template_string(html_content)

if __name__ == '__main__':
    app.run(debug=True)
