from database_util import connect_db,get_all_cleaned_htmls_to_extract
import datetime

def gethtml(tender_id):
    # 连接数据库
    db = connect_db()
    if db is None:
        print("Failed to connect to the database.")
        return
    # 创建游标
    cursor = db.cursor()
    # 获取当前tender_id下，tender_detail_html表中的cleaned_detail_html字段
    cursor.execute("SELECT tender_id, cleaned_detail_html FROM tender_detail_html WHERE tender_id = %s", (tender_id,))
    result = cursor.fetchone()
    # print(result)
    print("LOAD SQL SUCCESS")
    # 关闭游标和数据库连接
    cursor.close()
    db.close()
    if result is not None:
        return result[1]
        print("SQL gethtml"+tender_id+" SUCCESS AND CLOSED")
    else:
        return None

from zhipuai import ZhipuAI
import json
import re

def getFormatedData(cleanedHtml):
    client = ZhipuAI(api_key="e6af334544b37a85e83900a9152eb9a0.GzjnBTUhPOhDDJhx")
    response = client.chat.completions.create(
    model="glm-4", 
    messages=[
         {"role": "user", "content": f"请根据以下清洗后的招标公告内容，提取招标相关的全部信息，并以键值对的形式返回这些信息。我需要以下字段：tender_id, tender_document_start_time, tender_document_end_time, question_deadline, answer_announcement_time, bid_submission_deadline, bid_opening_time, tenderer, tender_contact, contact_phone, tender_agency, tender_agency_contact, tender_agency_contact_phone, supervision_qualification_requirement, business_license_requirement, chief_supervisor_qualification_requirement, consortium_bidding_requirement, project_name, investment_project_code, tender_project_name, implementation_site, funding_source, tender_scope_and_scale, duration, maximum_bid_price, qualification_review_method。这些字段的内容是：{cleanedHtml}。请以以下的JSON格式返回结果：```json{{\"tender_id\": \"\", \"tender_document_start_time\": \"\", \"tender_document_end_time\": \"\", \"question_deadline\": \"\", \"answer_announcement_time\": \"\", \"bid_submission_deadline\": \"\", \"bid_opening_time\": \"\", \"tenderer\": \"\", \"tender_contact\": \"\", \"contact_phone\": \"\", \"tender_agency\": \"\", \"tender_agency_contact\": \"\", \"tender_agency_contact_phone\": \"\", \"supervision_qualification_requirement\": \"\", \"business_license_requirement\": \"\", \"chief_supervisor_qualification_requirement\": \"\", \"consortium_bidding_requirement\": \"\", \"project_name\": \"\", \"investment_project_code\": \"\", \"tender_project_name\": \"\", \"implementation_site\": \"\", \"funding_source\": \"\", \"tender_scope_and_scale\": \"\", \"duration\": \"\", \"maximum_bid_price\": \"\", \"qualification_review_method\": \"\"}}```。请注意，返回的结果应该是一个有效的JSON字符串，不应该包含任何特殊字符，不出现注释。某些值不存在或者没有提供则默认将这些值留空"}
    ],
    top_p=0.7,
    temperature=0.2,
    max_tokens=4096,
    )
    # print(response.choices[0].message)

    # 获取message的内容
    message_content = response.choices[0].message.content

   # 获取message的内容
    message_content = response.choices[0].message.content
    print("got message_content")

    # 去掉message_content中的特殊字符
    message_content_cleaned = message_content.split('```json')[1]
    # 去掉message_content中的特殊字符
    message_content_cleaned = message_content_cleaned.replace('\n', '').replace('\\', '').replace('`', '')
    
    # 使用正则表达式找到所有的注释
    comments = re.findall(r'//[^"\n]*', message_content_cleaned)
    # 使用正则表达式替换掉注释的 "//" 和其后的文字
    message_content_cleaned = re.sub(r'//[^"\n]*', '', message_content_cleaned)
    # 打印日志
    for comment in comments:
        print(f"Successfully removed comment: {comment}")
    
    # 找到最外层的 }
    count = 0
    for i, char in enumerate(message_content_cleaned):
        if char == '{':
            count += 1
        elif char == '}':
            count -= 1
            if count == 0:
                message_content_cleaned = message_content_cleaned[:i+1]
                break

    # 检查message_content_cleaned是否为空
    if not message_content_cleaned:
        print("Error: message_content_cleaned is empty.")
        return None

    # 使用json.loads将清洗后的字符串转换为字典
    try:
        formatedData = json.loads(message_content_cleaned)
    except json.JSONDecodeError as e:
        print(f"Error: failed to parse JSON: {message_content_cleaned}")
        print(f"JSONDecodeError: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    # 打印出data
    print("FORMATED DATA DONE,DATA print ...:")
    #  + json.dumps(formatedData)
    return formatedData




def insert_into_tender_detail(cursor, data):
    # 获取字段名和值
    fields = ', '.join(data.keys())
    values = ', '.join(['%s'] * len(data))

    # 创建占位符字符串
    placeholders = ', '.join(['%s'] * len(data))
    
    # 创建INSERT SQL语句
    insert_query = f"""INSERT INTO tender_detail ({fields}) VALUES ({values})"""
    
    
    # 执行SQL语句
    cursor.execute(insert_query, list(data.values()))
    print("inserting data into tender_detail")
    # +insert_query

def insertTenderDetail(tender_id, formatedData):
    # 连接数据库
    with connect_db() as db:
        if db is None:
            print("Failed to connect to the database.")
            return

         # 检查formatedData是否为None
        if formatedData is None:
            print("Error: formatedData is None.")
            return
        
        # 添加tender_id到formatedData字典中
        formatedData['tender_id'] = tender_id

        # 创建游标
        with db.cursor() as cursor:
            # 插入数据
            insert_into_tender_detail(cursor, formatedData)
            print("insert_into_tender_detail")
            # 提交事务
            db.commit()

def update_last_extracted_time(db,cursor, tender_id):
    # 更新最后提取时间
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    update_sql = "UPDATE tender_detail_html SET last_extracted_time = %s WHERE tender_id = %s"
    cursor.execute(update_sql, (now, tender_id))
    db.commit()

def main():
    # 连接数据库
    db = connect_db()
    # 创建游标
    cursor = db.cursor()
    print("connect db success")
    # 获取所有未提取或需要重新提取信息的HTML
    entries = get_all_cleaned_htmls_to_extract(cursor)

    for entry in entries:
        tender_id, cleaned_html = entry  # 使用解构来获取tender_id和cleaned_detail_html
        print(f"Processing tender_id: {tender_id}")
        # 如果cleanedHtml不为空，则处理数据并插入到数据库中
        if cleaned_html is not None:
            try:
                formatedData = getFormatedData(cleaned_html)
                print("getFormatedData")
                if formatedData is not None:  # 检查formatedData是否为None
                    insertTenderDetail(tender_id, formatedData)
                    print("insertTenderDetail")
                    # 更新最后提取时间
                    update_last_extracted_time(db, cursor, tender_id)
                    print("update_last_extracted_time")
                else:
                    print(f"Error processing tender_id: {tender_id}, formatedData is None.")
                    continue
            except Exception as e:
                print(f"Error processing tender_id: {tender_id}, error: {str(e)}")
                continue

    # 关闭游标和数据库连接
    cursor.close()
    db.close()
    print("db closed")

if __name__ == "__main__":
    main()
