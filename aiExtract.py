from database_util import connect_db,get_all_cleaned_htmls_to_extract,insert_data_into_tender_detail,update_last_extracted_time
from zhipuai import ZhipuAI
import json
import re
import logging

def getFormattedData(cleanedHtml):
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

    message_content = response.choices[0].message.content
    message_content_cleaned = message_content.split('```json')[1].replace('\n', '').replace('\\', '').replace('`', '')
    print("got message_content")

    
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

    return formatedData


def aiExtract():
    with connect_db() as db, db.cursor() as cursor:
        entries = get_all_cleaned_htmls_to_extract(cursor)
        logging.info(f"从数据库中获取了 {len(entries)} 条记录，准备进行AI提取。")

        for tender_id, cleaned_html in entries:
            if cleaned_html:
                try:
                    formattedData = getFormattedData(cleaned_html)
                    if formattedData:
                        formattedData['tender_id'] = tender_id  # 在这里添加 tender_id
                        insert_data_into_tender_detail(formattedData)  
                        update_last_extracted_time(db, cursor, tender_id)
                except Exception as e:
                    print(f"Error processing tender_id: {tender_id}, error: {str(e)}")

if __name__ == "__main__":
    aiExtract()
