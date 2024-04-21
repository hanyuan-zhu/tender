import difflib
from datetime import datetime
from zhipuai import ZhipuAI
import logging
import json
import re
from database_util import connect_db,insert_data_into_db,get_all_cleaned_htmls_to_extract_key



def convert_list_to_string(lst):
    return ', '.join(lst)


def extract_detail_from_html(html):
    client = ZhipuAI(api_key="fd2d2655211b3a9013cf1894f944cef6.BGkirapkKYOXU1zy")
    messages = []
    messages.append({"role": "user", "content": """用json格式整理下面是招标公告HTML信息 :"""})
    messages.append({"role": "user", "content": html})
    messages.append({"role": "user", "content": "至少包含下列信息："})
    messages.append({"role": "user", "content": """
                     招标价格，包含金额数值和单位，输出
                     \"招标价格\": {
                         \"金额\": 72.045483,
                         \"单位\": \"万元\"
                         }
                    """})
    messages.append({"role": "user", "content": '''
                     工期信息的表达形式可能包括“730日历天”，“34个月”，“2024-03-10至2024-09-06”或“自监理人收到中标通知书之日起算，至工程办妥竣工结算且保修期结束止”。请根据提供的信息格式化输出。例如，如果提供的工期是730日历天，则输出应该是：
                     "工期": "730日历天"
                     '''})
    messages.append({"role": "user", "content": "总建筑面积，包含数值和单位，输出：“总建筑面积”：{“面积数值：10000，单位：平方米”}"})
    messages.append({"role": "user", "content": "建安费，总投资中的建安费部分总额，输出：“建安费”：{金额：500，单位：万元}"})
    messages.append({"role": "user", "content": "监理企业资质要求，输出：“监理企业资质要求”：“房屋建筑工程甲级”"})
    messages.append({"role": "user", "content":'''
            总监的具体要求，输出："总监要求"：{
                "注册资格证书专业": "房屋建筑工程",
                "职称等级": "高级工程师",
                "学历": "硕士",
                "其他要求限制": "无"
            }'''
            })
    messages.append({"role": "user", "content": "如果信息不明确或未提及，请忽略相应的字段。"})
    response = client.chat.completions.create(
        model="glm-4", 
        messages=messages,
        temperature=0.1,
        max_tokens=8192,
    )
    # return response
    return response.choices[0].message.content

def ai_formatting_by_field(json_data):
    client = ZhipuAI(api_key="fd2d2655211b3a9013cf1894f944cef6.BGkirapkKYOXU1zy")
    messages = []
    messages.append({"role": "user", "content": """
    你是一个专门检查招标信息提取的AI。你的任务是验证字段是否依据要求输出，如果输出没有达到要求输出的格式，则调整输出成要求的格式内容。如果字段值不明确或者未提及，则输出 Null 作为该字段值。
    请根据以下信息进行检查：
                    """})
    messages.append({"role": "user", "content": json.dumps(json_data,ensure_ascii=False)})
    messages.append({"role": "user", "content": "你以下是各自段的输出格式要求："})
    
    for field, value in json_data.items():
        if field == "招标价格":
            messages.append({"role": "user", "content": '''招标价格，如”招标金额170081元“，则输出{"bid_price_value"：170081，"bid_price_unit"："元"}，金额和单位以实际招标价格为准'''})
        elif field =="工期":
            messages.append({"role": "user", "content": '''
                        工期根据以下格式的输出：
                        - 日历天数，如“730日历天”，则输出：{"period_type": "days", "duration": "730"}
                        - 月数，如“34个月”，则输出：{"period_type": "months", "duration": "34"}
                        - 具体日期范围，如“2024-03-10 至 2024-09-06”，则输出：{"period_type": "specific_dates", "start_date": "2024-03-10", "end_date": "2024-09-06"}
                        - 不明确的时间范围描述，如“自监理人收到中标通知书之日起算，至工程办妥竣工结算且保修期结束止”，则输出：{"period_type": "undefined", "description": "自监理人收到中标通知书之日起算，至工程办妥竣工结算且保修期结束止"}
                        
                        输出仅包含一类时间范围描述，不会同时出现多个时间范围描述。如果时间范围描述不明确或未提及，则输出：{"period_type": "undefined", "description": "未提及"}
                        '''})
        elif field =="总建筑面积":
            messages.append({"role": "user", "content": '''总建筑面积如“10000平方米”，则输出：{"total_area": 10000, "area_unit": "平方米"}'''})
        elif field =="建安费":
            messages.append({"role": "user", "content": '''“建安费”如“建安费500万元”，则输出：{"total_cost": 500, "cost_unit": "万元"}'''})
        elif field =="监理企业资质要求":
            messages.append({"role": "user", "content":'''
                             监理企业资质要求信息，并按以下规则生成输出：
                            - 特定专业资质优先于综合资质。如果一个要求中同时提到了综合资质和特定专业的资质等级，只记录特定专业的最低资质等级。
                            - 综合资质仅在没有具体专业资质要求时记录。它是覆盖所有专业的最高资质。
                            - 输出示例：
                            - 特定要求是房屋建筑工程的乙级，输出：{"qualification_type": "房屋建筑工程", "qualification_level": "乙级"}
                            - 综合资质是唯一要求时，输出：{"qualification_type": "综合资质", "qualification_level": "无"}
                            - 如果同时要求综合资质和房屋建筑工程的甲级，仅记录房屋建筑工程甲级：{"qualification_type": "房屋建筑工程", "qualification_level": "甲级"}
                            - 资质名称必须是来自于以下列表：房屋建筑工程、冶炼工程、矿山工程、化工石油工程、水利水电工程、电力工程、农林工程、铁路工程、公路工程、港口与航道工程、航天航空工程、通信工程、市政公用工程、机电安装工程，综合资质。
                    ''' })
        elif field =="总监要求":
            messages.append({"role": "user", "content": '''
                            总监要求下，以下信息待确认，
                            - 注册资格证书专业（必须确认，且必须为以下国家规定的专业之一）：房屋建筑工程; 冶炼工程; 矿山工程; 化工石油工程; 水利水电工程; 电力工程; 农林工程; 铁路工程; 公路工程; 港口与航道工程; 航天航空工程; 通信工程; 市政公用工程; 机电安装工程; 道路与桥梁; 隧道工程; 公路机电工程; 港口工程; 航道工程; 水运机电工程; 水利工程施工监理; 水土保持工程施工监理; 机电及金属结构设备制造监理; 水利工程建设环境保护监理;
                            - 职称等级（非必需，必须为以下国家规定的职级之一）：教授级高级工程师；高级工程师；工程师；助理工程师
                            - 学历要求（非必需）：仅记录最低学历要求，例如，”大专“，"本科"，“硕士”，“博士”
                            - 相关业绩要求（非必需）：如果明确提及的业绩项数，例如，“至少担任过2项类似工程的监理负责人”。
                            - 同时任职项目数量限制（非必需）：如果明确提及的项目数，例如，“在任职期间能参与的其他在施项目不得超过2个”。
                            示例输出（如果描述明确）：{
                            "qualification_profession": ["房屋建筑工程","电力工程"]
                            "title_level": "高级工程师",
                            "education": "硕士",
                            "performance_requirements": 3,
                            "simultaneous_projects_limit": 2
                            }
                            如果信息不明确或未提及，请忽略相应的字段
                            '''})

    messages.append({"role": "user", "content": "注意：严格按照要求格式输出，仅json。如果输出没有达到要求的格式，则调整输出成要求的格式（特别是字段名，一定严格用英文字段名）。如果字段值不明确或者未提及，则输出 Null 作为该字段值。"})
    response = client.chat.completions.create(
        model="glm-4", 
        messages=messages,
        temperature=0.1,
        max_tokens=8192,
    )
    return response.choices[0].message.content

def formating_by_field(input_dict):
    # 使用ai_formatting_by_field函数格式化输入字典
    input_string = ai_formatting_by_field(input_dict)
    
    # 尝试匹配Markdown代码块中的JSON
    pattern = r"```json\n(.*?)\n```"
    match = re.search(pattern, input_string, re.DOTALL)
    if match:
        json_string = match.group(1)
    else:
        # 如果没有找到代码块，使用整个字符串作为JSON字符串
        json_string = input_string.strip()
    
    try:
        # 尝试解析JSON字符串
        json_data = json.loads(json_string)
        return json_data
    except json.JSONDecodeError:
        # 如果解析失败，尝试将单引号替换为双引号后再次解析
        try:
            json_string = json_string.replace("'", "\"")
            json_data = json.loads(json_string)
            return json_data
        except json.JSONDecodeError:
            # 如果再次解析失败，返回错误信息
            return "Failed to decode JSON."
        
def convert_to_yuan(input_dict):
    # 检查输入的字典是否包含需要的键
    if 'value' in input_dict and 'unit' in input_dict:
        amount = input_dict['value']
        unit = input_dict['unit']

        # 检查金额是否为空或者为None
        if amount is None:
            logging.error("金额值为空")
            return None

        # 如果金额是字符串，尝试去除逗号并转换为浮点数
        if isinstance(amount, str):
            try:
                amount = float(amount.replace(",", ""))
            except ValueError:
                logging.error("金额值必须能转换为数字，输入的金额为：%s", amount)
                return None
        elif not isinstance(amount, (float, int)):
            logging.error("金额值的类型不正确，必须为数字，输入类型为：%s", type(amount).__name__)
            return None

        normalized_unit = unit.strip().replace(" ", "").lower()

        conversion_factors = {
            '元': 1,
            '万元': 10000,
            '亿元': 100000000
        }

        if normalized_unit not in conversion_factors:
            logging.error("不支持的金额单位：%s", unit)
            return None

        # 转换金额到元，并保留两位小数
        return float(round(amount * conversion_factors[normalized_unit], 2))

    else:
        logging.error("输入的字典中缺少'value'或'unit'键")
        return None
    
def convert_to_square_meters(input_dict):
    # 检查输入的字典是否包含需要的键
    if 'total_area' in input_dict and 'area_unit' in input_dict:
        area = input_dict['total_area']
        unit = input_dict['area_unit']

        if area is None:
            logging.error("面积值为空")
            return None

        if isinstance(area, str):
            try:
                area = float(area.replace(",", ""))
            except ValueError:
                logging.error("面积值必须能转换为数字，输入的面积为：%s", area)
                return None
        elif not isinstance(area, (float, int)):
            logging.error("面积值的类型不正确，必须为数字，输入类型为：%s", type(area).__name__)
            return None

        normalized_unit = unit.strip().replace(" ", "").lower()

        conversion_factors = {
            '平方米': 1,
            '亩': 666.67,
            '公顷': 10000,
            '万平方米': 10000,
            '平方公里': 1000000,
            '亿平方米': 100000000,
            '平方千米': 1000000
        }

        if normalized_unit not in conversion_factors:
            logging.error("不支持的面积单位：%s", unit)
            return None

        converted_area = area * conversion_factors[normalized_unit]
        return float(round(converted_area, 0))

    else:
        logging.error("输入的字典中缺少'total_area'或'area_unit'键")
        return None

def find_closest_match(input_type, valid_types):
    # 首先检查是否有完全匹配
    if input_type in valid_types:
        return input_type
    
    # 没有完全匹配，使用difflib找到最相似的匹配
    closest_match = difflib.get_close_matches(input_type, valid_types, n=1, cutoff=0.6)
    
    if closest_match:
        return closest_match[0]
    else:
        return None

valid_types = {
    'qualification_type':[
        "房屋建筑工程", "冶炼工程", "矿山工程", "化工石油工程", "水利水电工程",
        "电力工程", "农林工程", "铁路工程", "公路工程", "港口与航道工程",
        "航天航空工程", "通信工程", "市政公用工程", "机电安装工程", "综合资质"
    ],
    'qualification_profession': [
        "房屋建筑工程", "冶炼工程", "矿山工程", "化工石油工程", "水利水电工程", "电力工程", 
        "农林工程", "铁路工程", "公路工程", "港口与航道工程", "航天航空工程", "通信工程", 
        "市政公用工程", "机电安装工程", "道路与桥梁", "隧道工程", "公路机电工程", "港口工程", 
        "航道工程", "水运机电工程", "水利工程施工监理", "水土保持工程施工监理", 
        "机电及金属结构设备制造监理", "水利工程建设环境保护监理"
    ],
    'title_level': [
        "教授级高级工程师","高级工程师","工程师","助理工程师",
    ],
    'education': [
        "大专","本科","硕士","博士",
    ]
}

def convert_to_days(period_info):
    # 从raw_tender_key_detail表中，
    # - 能转化成天的工期就转化成 “天数”，
    # - 不能转化成天的就 “None”。
    try:
        if period_info['period_type'] == 'days':
            return int(period_info['duration'])
        elif period_info['period_type'] == 'months':
            return int(period_info['duration']) * 30
        elif period_info['period_type'] == 'specific_dates':
            start_date = datetime.strptime(period_info['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(period_info['end_date'], '%Y-%m-%d')
            delta = end_date - start_date
            return delta.days
        else:
            return None
    except (ValueError, TypeError) as e:
        # 记录错误信息
        logging.warning(f"‘convert_to_days’ returned None. Processing {period_info['period_type']} with values {period_info}. Error value: {e}")
        return None

def process_key(key, key_dict, valid_types):
    if key == "招标价格":
        key_dict = {'value': key_dict['bid_price_value'], 'unit': key_dict['bid_price_unit']}
        key_dict = {'bid_price': convert_to_yuan(key_dict)}
    elif key == "建安费":
        key_dict = {'value': key_dict['total_cost'], 'unit': key_dict['cost_unit']}
        key_dict = {'construction_cost': convert_to_yuan(key_dict)}
    elif key == "工期":
        key_dict = {'construction_duration': convert_to_days(key_dict)}
    elif key == "总建筑面积":
        key_dict = {'construction_area': convert_to_square_meters(key_dict)}
    elif key in ["监理企业资质要求"]:
        for field in ['qualification_type']:
            if field in key_dict:
                input_type = key_dict.get(field)
                if input_type:
                    closest_match = find_closest_match(input_type, valid_types.get(field, []))
                    key_dict[field] = closest_match
    elif key == "总监要求":
        for field in ['title_level', 'education', 'qualification_profession']:
            if field in key_dict:
                input_type = key_dict.get(field)
                if input_type is not None:
                    if isinstance(input_type, list):
                        for i, profession in enumerate(input_type):
                            if i > 1:
                                raise ValueError("Too many professions in 'qualification_profession'")
                            closest_match = find_closest_match(profession, valid_types.get(field, []))
                            if i == 0:
                                key_dict['qualification_profession'] = closest_match
                            else:
                                key_dict['qualification_profession_addition'] = closest_match 
                    else:
                        closest_match = find_closest_match(input_type, valid_types.get(field, []))
                        key_dict[field] = closest_match


    return key_dict

def extract_json_from_html(html_content):
    extracted_msg = extract_detail_from_html(html_content)
    # 使用正则表达式提取JSON字符串
    match = re.search('```json\n(.*)\n```', extracted_msg, re.DOTALL)
    if match is None:
        # 没有找到匹配的字符串，返回一个空的字典
        return {}
    json_string = match.group(1)
    # 将JSON字符串转换为Python字典
    json_dict = json.loads(json_string)
    return json_dict

def process_html_data(html,valid_types):
    try:
        json_dict = extract_json_from_html(html[1])
        raw_tender_dict = {"tender_id": html[0]}
        post_processed_dict = {"tender_id": html[0]}

        # 上述 json_dict 的输出才是多层级的。（从cleaned_html第一次提取）
        # “招标价格”，“工期”，“总建筑面积”，“建安费”，“监理企业资质要求”，“总监要求”这些都是json_dict的key
        
        # 这里 raw_data和processed_data都是都是单一层级了。（ai_formatting处理后，从多层级json的第二次提取）
        # raw_data的数据结构是:{"tender_id":"xxx","bid_price_value": 100, "bid_price_unit": "万元"}
        # processed_data的数据结构是:{"tender_id":"xxx","bid_price": 10000}

        for key, value in json_dict.items():
            if value is not None:
                key_dict = {key: value}
                key_dict = formating_by_field(key_dict)
                # 注意：这里formating_by_field的后处理只保证了json格式，但不保证 key_value的格式，比如始末时间可能是由文字组成的string。
                raw_tender_dict.update(key_dict)
                
                try:
                    key_dict = process_key(key, key_dict, valid_types)
                    post_processed_dict.update({k: v for k, v in key_dict.items() if v is not None})
                except Exception as e:
                    print(f"Error processing key {key}: {e}")
                    continue
        
        return (raw_tender_dict, post_processed_dict)
    except Exception as e:
        logging.error(f"Error processing HTML for tender {html[0]}: {e}")
        return (None, None)

def aiKeyElementExtract():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    db = connect_db()
    if not db:
        logging.error("Failed to connect to the database.")
        return

    cursor = db.cursor()
    try:
        cleaned_htmls = get_all_cleaned_htmls_to_extract_key(cursor) 
        logging.info(f"Found {len(cleaned_htmls)} tenders to process.")
        #添加计算还有多少html要处理
        count_left = len(cleaned_htmls)
        for html in cleaned_htmls:
            
            count_left -= 1
            logging.info(f"还有{count_left}个html要处理")
            
            logging.info(f"Processing tender {html[0]}...")
            # 理论上这里 raw_data和processed_data都是 ai处理完之后的数据，都是json格式,且都没有多层级的数据，都是单一层级了。
            # raw_data的数据结构是:{"tender_id":"xxx","bid_price_value": 100, "bid_price_unit": "万元"}
            # processed_data的数据结构是:{"tender_id":"xxx","bid_price": 10000}
            raw_data, processed_data = process_html_data(html,valid_types)
            
            # Convert list values to strings
            for key, value in raw_data.items():
                if isinstance(value, list):
                    raw_data[key] = convert_list_to_string(value)

            if raw_data and processed_data:
                result = insert_data_into_db(db, cursor, raw_data, processed_data)
                if result is None:
                    logging.error("insert_data_into_db returned None, expected (db, cursor).")
                    continue
                db, cursor = result

                if db is None:
                    logging.error("Reconnection failed. Skipping insertion for this tender.")
                    continue  # Skip this tender and continue with the next
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
        
if __name__ == "__main__":
    aiKeyElementExtract()
    
    
    
