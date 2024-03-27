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
            "description": "提取招标公告中的重点信息，如项目名称、项目地点、施工内容与监理范围等",
            "parameters": {
            "type": "object",
            "properties": {
                "tender_project_name": {"description": "完整的项目名称", "type": "string"},
                "implementation_site": {"description": "具体的项目实施地点", "type": "string"},
                "scope_and_range": {"description": "工程项目概括及施工类型、监理服务范围", "type": "string"},
                "gross_floor_area": {"description": "项目的总建筑面积", "type": "string"},
                "total_investment": {"description": "项目总投资金额", "type": "string"},
                "duration": {"description": "工程预计完成时间（日历天，月份，或起始和终止日期）", "type": "string"},
                "bid_price": {"description": "用于表示项目监理服务费用或监理服务最高报价限制", "type": "string"},
                "bid_price_rate": {"description": "表示计算最终监理服务费用的系数或比例，以小数表示", "type": "string"},
                "company_qualification_requirement": {"description": "包括资质类型和资质等级要求", "type": "string"},
                "chief_registration_certificate": {"description": "注册监理工程师资格证书专业要求", "type": "string"},
                "chief_title_and_education": {"description": "总监的职称要求和学历要求", "type": "string"},
                "chief_experience": {"description": "总监类似项目方面业绩要求，要求候选人至少成功监理过特定数量的相似类型工程", "type": "string"},
                "chief_restrictions": {"description": "总监任职限制，如不允许同时监理多个项目", "type": "string"},
                "tenderer": {"description": "招标方的名称", "type": "string"},
                "bid_opening_time": {"description": "开标仪式的具体时间以年月日时分表示", "type": "string"}
            },
            "required": [
                "tender_project_name",
                "implementation_site",
                "scope_and_range",
                "gross_floor_area",
                "total_investment",
                "duration",
                "bid_price",
                "bid_price_rate",
                "company_qualification_requirement",
                "chief_registration_certificate",
                "chief_title_and_education",
                "chief_experience",
                "chief_restrictions",
                "tenderer",
                "bid_opening_time"
            ]
            }
        }
        }]

    # 清空对话
    messages = []

    messages.append({"role": "assistant", "content": """
                     你的任务是提取招标公告中的重点信息，用于将其插入到数据库中。
                     请注意：列出的字段数据都非常重要，务必全文仔细查找，涵盖所有字段。
                     以下是招标公告：{html}
                     """})
    # 你的任务是提取以下HTML招标公告中的全部信息，并将其插入到数据库中。
    # 请注意：招标公告的所有内容都非常重要，务必涵盖所有信息，遇到不清晰的信息时，进行合理推断。
    # messages.append({"role": "user", "content": "下面是招标公告内容："})
    # messages.append({"role": "user", "content": html})



    
    response = client.chat.completions.create(
        model="glm-4", 
        messages=messages,
        tools=tools,
        # tool_choice="auto",
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




                


