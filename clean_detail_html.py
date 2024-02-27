from bs4 import BeautifulSoup
from database_util import connect_db, get_uncleaned_html_records, update_cleaned_html


def clean_detail_html(html_content):
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

    return str(soup)


def clean_and_update_html():
    # 连接数据库
    db = connect_db()
    if db is None:
        print("Failed to connect to the database.")
        return

    # 创建游标
    cursor = db.cursor()

    # 获取所有未清洗的HTML记录
    records = get_uncleaned_html_records(cursor)

    for record in records:
        id, original_html = record
        # 清洗HTML
        cleaned_html = clean_detail_html(original_html)
        # 更新数据库
        update_cleaned_html(cursor, cleaned_html, id)

    # 提交事务
    db.commit()

    # 关闭数据库连接
    db.close()


if __name__ == "__main__":
    clean_and_update_html()