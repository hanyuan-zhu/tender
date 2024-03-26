# Description: 从数据库中获取所有未提取或需要重新提取信息的HTML，使用AI提取招标详细信息，并将提取的信息插入到数据库中。

from zhipuai import ZhipuAI
from database_util import connect_db,get_all_cleaned_htmls_to_extract,update_last_extracted_time,insert_data_into_tender_detail
import json
import logging
# 配置日志级别，输出位置等
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_detail_from_html(html):

    client = ZhipuAI(api_key="e6af334544b37a85e83900a9152eb9a0.GzjnBTUhPOhDDJhx")
    
    tools = [{
        "type": "function",
        "function": {
            "name": "get_tender_detail",
            "description": "将招标详细信息插入到数据库中",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"description": "项目名称", "type": "string"},
                    "investment_project_code": {"description": "项目的唯一代码", "type": "string"},
                    "tender_project_name": {"description": "招标项目名称", "type": "string"},
                    "implementation_site": {"description": "具体的项目实施地点", "type": "string"},
                    "funding_source": {"description": "项目资金的来源说明", "type": "string"},
                    "tender_scope_and_scale": {"description": "详细的范围和规模描述，包括建筑面积、总投资额。", "type": "string"},
                    "duration": {"description": "工程预计完成时间（日历天，月份，或起始和终止日期）", "type": "string"},
                    "maximum_bid_price": {"description": "招标价格和费率：招标价格或最高价格限制，必须标明单位（例如，100万元），以及收费系数或报价费率是百分比（例如，80%）", "type": "string"},
                    "business_license_requirement": {"description": "必要的营业执照说明", "type": "string"},
                    "supervision_qualification_requirement": {"description": "资质类型和资质最低等级要求", "type": "string"},
                    "chief_supervisor_qualification_requirement": {"description": "总监资格要求，包括但不限于资格证书专业，职称最低要求，学历最低要求，总监业绩要求，在职项目限制等等。", "type": "string"},
                    "consortium_bidding_requirement": {"description": "关于联合体投标的具体要求", "type": "string"},
                    "qualification_review_method": {"description": "资格审查的具体方法", "type": "string"},
                    "tenderer": {"description": "招标方的名称", "type": "string"},
                    "tender_contact": {"description": "招标方的联系人姓名", "type": "string"},
                    "contact_phone": {"description": "联系人的电话号码", "type": "string"},
                    "tender_agency": {"description": "被委托的招标代理机构名称", "type": "string"},
                    "tender_agency_contact": {"description": "招标代理的联系人姓名", "type": "string"},
                    "tender_agency_contact_phone": {"description": "招标代理联系人的电话号码", "type": "string"},
                    "tender_document_start_time": {"description": "获取招标文件截止时间", "type": "string"},
                    "tender_document_end_time": {"description": "获取招标文件截止时间以年月日时分表示", "type": "string"},
                    "question_deadline": {"description": "提出疑问的截止时间以年月日时分表示", "type": "string"},
                    "answer_announcement_time": {"description": "答疑公告的发布时间以年月日时分表示", "type": "string"},
                    "bid_submission_deadline": {"description": "提交投标文件的截止时间以年月日时分表示", "type": "string"},
                    "bid_opening_time": {"description": "开标仪式的具体时间以年月日时分表示", "type": "string"}
                    },
                "required": [
                    'project_name',
                    'investment_project_code',
                    'tender_project_name',
                    'implementation_site',
                    'funding_source',
                    'tender_scope_and_scale',
                    'duration',
                    'maximum_bid_price',
                    'business_license_requirement',
                    'supervision_qualification_requirement',
                    'chief_supervisor_qualification_requirement',
                    'consortium_bidding_requirement',
                    'qualification_review_method',
                    'tenderer',
                    'tender_contact',
                    'contact_phone',
                    'tender_agency',
                    'tender_agency_contact',
                    'tender_agency_contact_phone',
                    'tender_document_start_time',
                    'tender_document_end_time',
                    'question_deadline',
                    'answer_announcement_time',
                    'bid_submission_deadline',
                    'bid_opening_time'
                    ]
                }
            }
        }]

    # 清空对话
    messages = []

    messages.append({"role": "system", "content": """
                     你的任务是提取以下HTML招标公告中的全部信息，并将其插入到数据库中。
                     请注意：招标公告的所有内容都非常重要，务必涵盖所有信息，遇到不清晰的信息时，进行合理推断。
                     """})
    messages.append({"role": "user", "content": "下面是招标公告内容："})
    messages.append({"role": "user", "content": html})



    
    response = client.chat.completions.create(
        model="glm-4", 
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "get_tender_detail"}},
        top_p=0.7,
        temperature=0.95,
        max_tokens=4096,
    )
    
    logging.info("提取HTML招标详情的响应: {}".format(response))

    
    return response


def preprocess_data(tender_id, data):
    processed_data = {key: None if isinstance(value, dict) else value for key, value in data.items()}
    processed_data['tender_id'] = tender_id  
    return processed_data

def insert_detail_data(tender_id, data):
    processed_data = preprocess_data(tender_id, data)
    insert_data_into_tender_detail(processed_data)
                

def detail_extract(tender_id, html):
    logging.info(f"开始处理 tender_id 为 {tender_id} 的记录")
    # detail_json = extract_detail_from_html(html).choices[0].message.tool_calls[0].function.arguments
    # logging.info(f"提取的JSON字符串: {detail_json}")
    # data = json.loads(detail_json.replace("'", "\""))
    # logging.info(f"解析后的数据: {data}")
    # insert_detail_data(tender_id, data)
    # logging.info(f"完成处理 tender_id 为 {tender_id} 的记录")

    detail_response = extract_detail_from_html(html)
    if detail_response.choices and detail_response.choices[0].message.tool_calls:
        detail_json = detail_response.choices[0].message.tool_calls[0].function.arguments
        logging.info(f"提取的JSON字符串: {detail_json}")
        try:
            data = json.loads(detail_json.replace("'", "\""))
            logging.info(f"解析后的数据: {data}")
            insert_detail_data(tender_id, data)
            logging.info(f"完成处理 tender_id 为 {tender_id} 的记录")
        except Exception as e:
            logging.error(f"解析JSON时出错: {e}")
    else:
        logging.error("无法从响应中提取详细信息，可能是因为返回结果为None或不完整。")


def aiExtractBackup():
    db = connect_db()
    cursor = db.cursor()

    # 获取所有未提取或需要重新提取信息的HTML
    entries = get_all_cleaned_htmls_to_extract(cursor)
    logging.info(f"从数据库中获取了 {len(entries)} 条记录，进行AI提取, by aiExtract.py.")

    for entry in entries:
        logging.info(f"正在处理第 {entry[0]} 条记录")

        tender_id = entry[0]  # 使用索引0来获取tender_id
        cleaned_html = entry[1]  # 使用索引1来获取cleaned_detail_html
        
        try:
            # 提取详情并插入到tender_detail表中
            detail_extract(tender_id, cleaned_html)
            # 更新最后提取时间
            update_last_extracted_time(db,cursor, tender_id)
        except Exception as e:
            logging.error(f"处理 tender_id 为 {tender_id} 的记录时出错: {e}")
            continue  # 发生错误时跳过当前记录，继续处理下一条


    # 关闭游标和数据库连接
    cursor.close()
    db.close()
    logging.info("所有记录处理完毕")
    pass

if __name__ == "__main__":
    aiExtractBackup()




                


