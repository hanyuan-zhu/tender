from zhipuai import ZhipuAI
from database_util import connect_db,get_all_cleaned_htmls_to_extract
import datetime
import json
from mysql.connector import Error


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



    client = ZhipuAI(api_key="8d55d03f87e0ff621db27c37325c516d.4Ck0uvE4M1xYW8HB")
    
    template = """
            项目基本信息：
            - 项目ID (整型): 唯一标识符
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
            """


    # 清空对话
    messages = []

    messages.append({"role": "system", "content": "你的任务是提取以下HTML招标公告中的信息，并按照提供的模版格式化输出为一个Python字典。如果HTML中缺少某些信息，请在相应字段中标记为“信息缺失”。如果HTML中包含模版中未列出的新信息，请添加新字段和值。招标公告 HTML:"})
    
    messages.append({"role": "user", "content": html})

    messages.append({"role": "system", "content": "请按照以下模版格式化提取信息，并将信息添加到数据表中："})

    messages.append({"role": "system", "content": template})


    
    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=messages,
        # tools=tools,
        top_p=0.7,
        temperature=0.5,
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


    client = ZhipuAI(api_key="8d55d03f87e0ff621db27c37325c516d.4Ck0uvE4M1xYW8HB")
    tools = [{
        "type": "function",
        "function": {
            "name": "get_tender_detail",
            "description": "将招标详细信息插入到数据库中",
            "parameters": {
                "type": "object",
                "properties": {
                    "tender_document_start_time": {"description": "获取招标文件开始时间", "type": "string"},
                    "tender_document_end_time": {"description": "获取招标文件截止时间", "type": "string"},
                    "question_deadline": {"description": "提疑截止时间", "type": "string"},
                    "answer_announcement_time": {"description": "答疑公告时间", "type": "string"},
                    "bid_submission_deadline": {"description": "递交投标文件截止时间", "type": "string"},
                    "bid_opening_time": {"description": "开标时间", "type": "string"},
                    "tenderer": {"description": "招标人", "type": "string"},
                    "tender_contact": {"description": "招标人联系人", "type": "string"},
                    "contact_phone": {"description": "联系电话", "type": "string"},
                    "tender_agency": {"description": "招标代理机构", "type": "string"},
                    "tender_agency_contact": {"description": "招标代理联系人", "type": "string"},
                    "tender_agency_contact_phone": {"description": "招标代理联系电话", "type": "string"},
                    "supervision_qualification_requirement": {"description": "监理资质要求", "type": "string"},
                    "chief_supervisor_qualification_requirement": {"description": "总监理工程师资格要求", "type": "string"},
                    "consortium_bidding_requirement": {"description": "联合体投标要求", "type": "string"},
                    "project_name": {"description": "项目名称", "type": "string"},
                    "investment_project_code": {"description": "投资项目代码", "type": "string"},
                    "tender_project_name": {"description": "招标项目名称", "type": "string"},
                    "implementation_site": {"description": "实施地点", "type": "string"},
                    "funding_source": {"description": "资金来源", "type": "string"},
                    "tender_scope_and_scale": {"description": "招标范围及规模", "type": "string"},
                    "duration": {"description": "工期", "type": "string"},
                    "maximum_bid_price": {"description": "最高投标限价", "type": "number"},
                    "qualification_review_method": {"description": "资格审查方式", "type":  "string"}
                    },
                "required": [
                    "tenderer",
                    "tender_contact",
                    "contact_phone",
                    "tender_agency",
                    "tender_agency_contact",
                    "tender_agency_contact_phone",
                    "supervision_qualification_requirement",
                    "chief_supervisor_qualification_requirement",
                    "consortium_bidding_requirement",
                    "project_name",
                    "investment_project_code",
                    "tender_project_name",
                    "funding_source",
                    "tender_scope_and_scale",
                    "duration",
                    "maximum_bid_price",
                    "qualification_review_method"
                    ]
                }
            }
        }]


    # 清空对话
    messages = []

    messages.append({"role": "system", "content": """将下面的招标公告（html）中的,"招标人","项目名称","工期","最高投标限价"等,所有要求的信息插入数据库。"""})
    messages.append({"role": "user", "content":"""
                    下面是"招标公告"内容:
                    """})

    messages.append({"role": "user", "content": html})

    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=messages,
        tools=tools,
        top_p=0.7,
        temperature=0.5,
        max_tokens=4096,
    )

    return response


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

            # insert_query = f"""
            # INSERT INTO {TENDER_DETAIL_TABLE_NAME} (tender_id, project_name, tender_project_name, tender_document_start_time, tender_document_end_time, question_deadline, answer_announcement_time, bid_submission_deadline, bid_opening_time, tenderer, tender_contact, contact_phone, tender_agency, tender_agency_contact, tender_agency_contact_phone, supervision_qualification_requirement, chief_supervisor_qualification_requirement, consortium_bidding_requirement, investment_project_code, funding_source, tender_scope_and_scale, duration, maximum_bid_price, qualification_review_method)
            # VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            # """
            insert_query = f"""
            INSERT INTO tender_detail (tender_id, tender_document_start_time, tender_document_end_time, question_deadline, answer_announcement_time, bid_submission_deadline, bid_opening_time, tenderer, tender_contact, contact_phone, tender_agency, tender_agency_contact, tender_agency_contact_phone, supervision_qualification_requirement, business_license_requirement, chief_supervisor_qualification_requirement, consortium_bidding_requirement, project_name, investment_project_code, tender_project_name, implementation_site, funding_source, tender_scope_and_scale, duration, maximum_bid_price, qualification_review_method) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # 构建参数列表，确保参数的顺序与SQL语句中的占位符顺序相匹配
            params = [
                tender_id,  # 从外部获取tender_id
                data.get('tender_document_start_time', None),
                data.get('tender_document_end_time', None),
                data.get('question_deadline', None),
                data.get('answer_announcement_time', None),
                data.get('bid_submission_deadline', None),
                data.get('bid_opening_time', None),
                data.get('tenderer', None),
                data.get('tender_contact', None),
                data.get('contact_phone', None),
                data.get('tender_agency', None),
                data.get('tender_agency_contact', None),
                data.get('tender_agency_contact_phone', None),
                data.get('supervision_qualification_requirement', None),
                data.get('business_license_requirement', None),
                data.get('chief_supervisor_qualification_requirement', None),
                data.get('consortium_bidding_requirement', None),
                data.get('project_name', None),
                data.get('investment_project_code', None),
                data.get('tender_project_name', None),
                data.get('implementation_site', None),
                data.get('funding_source', None),
                data.get('tender_scope_and_scale', None),
                data.get('duration', None),
                data.get('maximum_bid_price', None),
                data.get('qualification_review_method', None)
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
    # this is the bulletpoint list of the extracted details (key-value pairs)
    detail_list = extract_detail_from_html(html).choices[0].message.content
    # tansform the bulletpoint list into a dictionary, ready for insertion into the database
    detail_json = detail_list_to_dict(detail_list).choices[0].message.tool_calls[0].function.arguments
    data = json.loads(detail_json.replace("'", "\""))
    insert_detail_data(tender_id, data)
    

def update_last_extracted_time(db,cursor, tender_id):
    # 更新最后提取时间
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    update_sql = "UPDATE tender_detail_html SET last_extracted_time = %s WHERE tender_id = %s"
    cursor.execute(update_sql, (now, tender_id))
    db.commit()


def main():
    db = connect_db()

    # 创建游标
    cursor = db.cursor()

    # 获取所有未提取或需要重新提取信息的HTML
    entries = get_all_cleaned_htmls_to_extract(cursor)

    for entry in entries:
        tender_id = entry[0]  # 使用索引0来获取tender_id
        cleaned_html = entry[1]  # 使用索引1来获取cleaned_detail_html
        
        # 提取详情并插入到tender_detail表中
        detail_extract(tender_id, cleaned_html)
        
        # 更新最后提取时间
        update_last_extracted_time(db,cursor, tender_id)

    # 关闭游标和数据库连接
    cursor.close()
    db.close()
    pass

if __name__ == "__main__":
    main()




                


