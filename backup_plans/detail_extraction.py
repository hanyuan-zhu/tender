from zhipuai import ZhipuAI
from database_util import connect_db,get_all_cleaned_htmls_to_extract
import datetime
import json
from mysql.connector import Error
import logging
# 配置日志级别，输出位置等
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def extract_detail_from_html(html):
    """
    这个函数的目的是从提供的HTML招标公告中提取信息，并将这些信息格式化为一个Python字典。

    参数:
    html (str): 输入的HTML招标公告。

    返回:
    response: 一个包含提取的信息的类字典信息。

    函数的工作流程如下：
    1. 创建一个ZhipuAI客户端实例。
    2. 定义一个模板，该模板列出了需要从HTML中提取的信息字段。
    3. 创建一个消息列表，该列表包含了系统和用户的对话内容，包括HTML招标公告和信息提取模板。
    4. 使用ZhipuAI客户端的chat.completions.create方法，将消息列表和模型参数作为输入，生成一个响应。这个响应包含了从HTML中提取的信息，格式化为一个Python字典。
    5. 返回这个响应。

    注意：这个函数依赖于ZhipuAI的API，需要提供有效的API密钥。
    """

    client = ZhipuAI(api_key="e6af334544b37a85e83900a9152eb9a0.GzjnBTUhPOhDDJhx")
    
    template = """
            项目基本信息：
            - 项目名称 (字符串): 详细的项目名称
            - 投资项目代码 (字符串): 项目的唯一代码
            - 招标项目名称 (字符串): 招标的详细名称
            - 实施地点 (字符串): 具体的项目实施地点
            - 资金来源 (字符串): 项目资金的来源说明
            - 招标范围及规模 (文本): 详细的范围和规模描述
            - 工期 (字符串): 工程预计完成时间
            - 最高投标限价 (浮点数): 投标的最高价格限制
            - 资格审查方式 (字符串): 资格审查的具体方法
            投标人资格要求：
            - 监理资质要求 (文本): 监理相关的资质要求
            - 营业执照要求 (文本): 必要的营业执照说明
            - 总监理工程师资格要求 (文本): 总监理工程师的资格条件
            - 联合体投标要求 (文本): 关于联合体投标的具体要求
            招标人和投标人信息：
            - 招标人 (字符串): 招标方的名称
            - 招标人联系人 (字符串): 招标方的联系人姓名
            - 联系电话 (字符串): 联系人的电话号码
            - 招标代理机构 (字符串): 被委托的招标代理机构名称
            - 招标代理联系人 (字符串): 招标代理的联系人姓名
            - 招标代理联系电话 (字符串): 招标代理联系人的电话号码
            投标时间表信息：
            - 获取招标文件开始时间 (字符串): 开始时间以年月日时分表示
            - 获取招标文件截止时间 (字符串): 截止时间以年月日时分表示
            - 提疑截止时间 (字符串): 提出疑问的截止时间以年月日时分表示
            - 答疑公告时间 (字符串): 答疑公告的发布时间以年月日时分表示
            - 递交投标文件截止时间 (字符串): 提交投标文件的截止时间以年月日时分表示
            - 开标时间 (字符串): 开标仪式的具体时间以年月日时分表示

            其他信息：
            - (待补充新字段...)
            """


    # 清空对话
    messages = []

    messages.append({"role": "system", "content": """
                     你的任务是提取以下HTML招标公告中的全部信息。
                     1. 根据模版填充相应的字段和值；
                     2. 若无法找到字段信息，则忽略该字段；
                     3. 若判断有全新的字段（未包含在模版中），则添加新字段和值。
                     """})
    messages.append({"role": "system", "content": """
                     注意：招标公告的所有内容都非常重要，务必涵盖所有信息，遇到不清晰的信息时，进行合理推断。
                     下面是目前的模版："""
                     })

    messages.append({"role": "system", "content": template})
    
    messages.append({"role": "user", "content": "下面是招标公告内容："})

    messages.append({"role": "user", "content": html})



    
    response = client.chat.completions.create(
        model="glm-4", 
        messages=messages,
        top_p=0.7,
        temperature=0.95,
        max_tokens=4096,
    )
    return response


def detail_list_to_dict(html):
    """
    这个函数的将 extract_detail_from_html 输出的招标信息列表转换为一个 Json 准备插入数据库。

    参数:
    html (str): extract_detail_from_html的输出。

    返回:
    response: 一个包含提取的信息的Python字典。

    函数的工作流程如下：
    1. 创建一个ZhipuAI客户端实例。
    2. 定义一个工具列表，该列表包含一个函数工具，该工具描述了如何从HTML中提取信息并将其插入到数据库中。
    3. 创建一个消息列表，该列表包含了系统和用户的对话内容，包括HTML招标公告。
    4. 使用ZhipuAI客户端的chat.completions.create方法，将消息列表和模型参数作为输入，生成一个响应。这个响应包含了从HTML中提取的信息，格式化为一个Python字典。
    5. 返回这个响应。

    注意：这个函数依赖于ZhipuAI的API，需要提供有效的API密钥。
    """


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
                    "investment_project_code": {"description": "投资项目代码", "type": "string"},
                    "tender_project_name": {"description": "招标项目名称", "type": "string"},
                    "implementation_site": {"description": "实施地点", "type": "string"},
                    "funding_source": {"description": "资金来源", "type": "string"},
                    "tender_scope_and_scale": {"description": "招标范围及规模", "type": "string"},
                    "duration": {"description": "工期", "type": "string"},
                    "maximum_bid_price": {"description": "最高投标限价", "type": "number"},
                    "business_license_requirement":{"description": "营业执照要求", "type": "string"},
                    "supervision_qualification_requirement": {"description": "监理资质要求", "type": "string"},
                    "chief_supervisor_qualification_requirement": {"description": "总监理工程师资格要求", "type": "string"},
                    "consortium_bidding_requirement": {"description": "联合体投标要求", "type": "string"},
                    "qualification_review_method": {"description": "资格审查方式", "type":  "string"},
                    "tenderer": {"description": "招标人", "type": "string"},
                    "tender_contact": {"description": "招标人联系人", "type": "string"},
                    "contact_phone": {"description": "联系电话", "type": "string"},
                    "tender_agency": {"description": "招标代理机构", "type": "string"},
                    "tender_agency_contact": {"description": "招标代理联系人", "type": "string"},
                    "tender_agency_contact_phone": {"description": "招标代理联系电话", "type": "string"},
                    "tender_document_start_time": {"description": "获取招标文件开始时间", "type": "string"},
                    "tender_document_end_time": {"description": "获取招标文件截止时间", "type": "string"},
                    "question_deadline": {"description": "提疑截止时间", "type": "string"},
                    "answer_announcement_time": {"description": "答疑公告时间", "type": "string"},
                    "bid_submission_deadline": {"description": "递交投标文件截止时间", "type": "string"},
                    "bid_opening_time": {"description": "开标时间", "type": "string"}
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
                     你的任务是将下面的招标公告的内容，用tools逐项填入数据库表格中。
                     注意：每一条数据内容都非常重要，请你务必仔细阅读，并完整填写。
                     """})
    messages.append({"role": "user", "content":"""
                    下面是"招标公告"内容:
                    """})
    messages.append({"role": "user", "content": html})

    response = client.chat.completions.create(
        model="glm-4", 
        messages=messages,
        tools=tools,
        top_p=0.7,
        temperature=0.5,
        max_tokens=4096,
    )

    return response


def get_value_or_none(data, key):
    value = data.get(key)
    if isinstance(value, dict):
        return None  # 如果是字典，返回None
    return value

def insert_detail_data(tender_id, data):
    """
    将招标详细信息插入到数据库中。
    参数:
    - tender_id: int, 招标ID。
    - data: dict, 要插入的数据，预期为一个字典，包含所有必要的招标详细信息字段。
    """

    connection = connect_db()
    if connection is not None:
        try:
            cursor = connection.cursor()
            data['tender_id'] = tender_id

            # #这个是保存到 tender_detail 正式表格的
            # insert_query = f"""
            # INSERT INTO tender_detail (tender_id, tender_document_start_time, tender_document_end_time, question_deadline, answer_announcement_time, bid_submission_deadline, bid_opening_time, tenderer, tender_contact, contact_phone, tender_agency, tender_agency_contact, tender_agency_contact_phone, supervision_qualification_requirement, business_license_requirement, chief_supervisor_qualification_requirement, consortium_bidding_requirement, project_name, investment_project_code, tender_project_name, implementation_site, funding_source, tender_scope_and_scale, duration, maximum_bid_price, qualification_review_method) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            # """
            # 这个是保存到copy的            
            insert_query = f"""
            INSERT INTO tender_detail_copy (tender_id, tender_document_start_time, tender_document_end_time, question_deadline, answer_announcement_time, bid_submission_deadline, bid_opening_time, tenderer, tender_contact, contact_phone, tender_agency, tender_agency_contact, tender_agency_contact_phone, supervision_qualification_requirement, business_license_requirement, chief_supervisor_qualification_requirement, consortium_bidding_requirement, project_name, investment_project_code, tender_project_name, implementation_site, funding_source, tender_scope_and_scale, duration, maximum_bid_price, qualification_review_method) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # 构建参数列表，对所有参数应用上述逻辑
            params = [
                tender_id,  # 假设这是从外部正确获取的
                get_value_or_none(data, 'tender_document_start_time'),
                get_value_or_none(data, 'tender_document_end_time'),
                get_value_or_none(data, 'question_deadline'),
                get_value_or_none(data, 'answer_announcement_time'),
                get_value_or_none(data, 'bid_submission_deadline'),
                get_value_or_none(data, 'bid_opening_time'),
                get_value_or_none(data, 'tenderer'),
                get_value_or_none(data, 'tender_contact'),
                get_value_or_none(data, 'contact_phone'),
                get_value_or_none(data, 'tender_agency'),
                get_value_or_none(data, 'tender_agency_contact'),
                get_value_or_none(data, 'tender_agency_contact_phone'),
                get_value_or_none(data, 'supervision_qualification_requirement'),
                get_value_or_none(data, 'business_license_requirement'),
                get_value_or_none(data, 'chief_supervisor_qualification_requirement'),
                get_value_or_none(data, 'consortium_bidding_requirement'),
                get_value_or_none(data, 'project_name'),
                get_value_or_none(data, 'investment_project_code'),
                get_value_or_none(data, 'tender_project_name'),
                get_value_or_none(data, 'implementation_site'),
                get_value_or_none(data, 'funding_source'),
                get_value_or_none(data, 'tender_scope_and_scale'),
                get_value_or_none(data, 'duration'),
                get_value_or_none(data, 'maximum_bid_price'),
                get_value_or_none(data, 'qualification_review_method')
            ]
            cursor.execute(insert_query, params)
            connection.commit()
        except Error as e:
            print(f"Error: {e}")
            connection.rollback()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                

def detail_extract(tender_id, html):
    logging.info(f"开始处理 tender_id 为 {tender_id} 的记录")
    # this is the bulletpoint list of the extracted details (key-value pairs)
    detail_list = extract_detail_from_html(html).choices[0].message.content
    # tansform the bulletpoint list into a dictionary, ready for insertion into the database
    detail_json = detail_list_to_dict(detail_list).choices[0].message.tool_calls[0].function.arguments
    data = json.loads(detail_json.replace("'", "\""))
    insert_detail_data(tender_id, data)
    logging.info(f"完成处理 tender_id 为 {tender_id} 的记录")

    

def update_last_extracted_time(db,cursor, tender_id):
    # 更新最后提取时间
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 临时 版本，保存到copy
    update_sql = "UPDATE tender_detail_html_copy SET last_extracted_time = %s WHERE tender_id = %s"
    # 正式的版本，保存到正式表格
    # update_sql = "UPDATE tender_detail_html SET last_extracted_time = %s WHERE tender_id = %s"
    cursor.execute(update_sql, (now, tender_id))
    db.commit()
    logging.info(f"更新 tender_id 为 {tender_id} 的最后提取时间")



def main():
    db = connect_db()

    # 创建游标
    cursor = db.cursor()

    # 获取所有未提取或需要重新提取信息的HTML
    entries = get_all_cleaned_htmls_to_extract(cursor)
    logging.info(f"从数据库中获取了 {len(entries)} 条记录")

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
    main()




                


