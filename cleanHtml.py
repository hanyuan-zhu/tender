from bs4 import BeautifulSoup
from database_util import connect_db, get_uncleaned_html_records, update_cleaned_html
import logging

# 配置日志级别，输出位置等
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def cleanDetailHtml(html_content):
    logging.info("开始清洗HTML")

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 移除所有<style>标签
    for style in soup("style"):
        style.decompose()

    # 移除所有元素的style属性
    for tag in soup.find_all(True):
        tag.attrs = {key: value for key, value in tag.attrs.items() if key != 'style'}

    # 移除所有不必要的标签和属性
    for tag in soup.find_all(True):
        # 移除特定的属性（如果有特定需要保留的属性，可以在这里指定）
        attrs_to_keep = ['href', 'src']  # 举例，如果你想保留链接和图片源
        tag.attrs = {key: value for key, value in tag.attrs.items() if key in attrs_to_keep}
        
        # 移除空标签（没有文本也没有子标签的）
        if not tag.text.strip() and not tag.contents:
            tag.decompose()

    # 移除特定标签（例如，<span>，如果它们不携带重要信息）
    for span in soup.find_all('span'):
        span.unwrap()

    # 移除<strong>标签但保留其内容
    for strong_tag in soup.find_all('strong'):
        strong_tag.unwrap()
    
    logging.info("完成清洗HTML")

    return str(soup)


def cleanAndUpdateHtml():
    logging.info("开始清洗和更新HTML")
    # 连接数据库
    db = connect_db()
    if db is None:
        print("Failed to connect to the database.")
        logging.error("无法连接到数据库")
        return

    # 创建游标
    cursor = db.cursor()

    # 获取所有未清洗的HTML记录
    records = get_uncleaned_html_records(cursor)
    logging.info(f"获取了 {len(records)} 条未清洗的HTML记录")


    for record in records:
        id, original_html = record
        logging.info(f"正在处理第 {id} 条记录")

        # 清洗HTML
        cleaned_html = cleanDetailHtml(original_html)
        # 更新数据库
        update_cleaned_html(cursor, cleaned_html, id)

    # 提交事务
    db.commit()

    # 关闭数据库连接
    db.close()


if __name__ == "__main__":
    cleanAndUpdateHtml()