# Description: 该脚本用于将招标公告的标题进行分类，并将分类结果插入到数据库中。

from zhipuai import ZhipuAI
import json
from database_util import connect_db,get_announcement_types, get_tender_title, insert_into_announcement_labels


client = ZhipuAI(api_key="e6af334544b37a85e83900a9152eb9a0.GzjnBTUhPOhDDJhx")

def tender_categorization(title):
    tools = [{
        "type": "function",
        "function": {
            "name": "get_tender_detail",
            "description": "判断标题是属于什么类型的公告，并插入到数据库。",
            "parameters": {
                "type": "object",
                "properties": {
                    "公告类型": {"description": "公告类型只能是'招标公告'、'资格审核公告'、'答疑公告'、'变更公告'、'澄清公告'和'其他'其中一个，且是唯一类型", "type": "string","enum":['招标公告','资格审核公告','答疑公告','变更公告','澄清公告','其他']}
                    },
                "required": [
                    '公告类型',
                    ]
                }
            }
        }]


    # 清空对话
    messages = []

    messages.append({"role": "system", "content": """
                    公告类型:
                    - 招标公告：正式邀请符合资格的投标人参与投标的公告，提供拟采购的货物、工程或工程服务的基本信息、投标条件等。
                    - 资格审核公告：在招标公告发布前，对潜在投标人的资格条件进行审查的过程，旨在确保只有满足条件的投标人能参与投标。
                    - 答疑公告：对潜在投标人提出的问题给出的官方回答,若无人提问,则公告无答疑。
                    - 变更公告：对先前发布的招标公告内容进行的正式更改,如更改投标截止日期、更改招标文件以及招标的暂停或终止等。
                    - 澄清公告：对招标文件中的具体信息进行澄清或修正的公告。
                    - 其他：不属于以上任何一类的时候。
                    """})

    messages.append({"role": "user", "content": "请基于以下公告名称，来判断公告类型，并将类型插入数据库："})

    messages.append({"role": "user", "content": title})

    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=messages,
        top_p=0.7,
        temperature=0.5,
        tools=tools,
        max_tokens=4096,
    )
    return response.choices[0].message.tool_calls[0].function.arguments


def tenderLabeling():
    db = connect_db()
    cursor = db.cursor()

    try:
        # 在程序开始时获取最新的类型列表
        announcement_types = get_announcement_types(cursor)

        # 当 tender_categorization 返回一个类型时
        titles = get_tender_title(cursor)
        total_titles = len(titles)
        for i, title in enumerate(titles):
            try:
                print(f"Processing title {i+1} of {total_titles}")
                type_temp = tender_categorization(title[1])
                tender_title_type = json.loads(type_temp.replace("'", "\""))
                announcement_type = tender_title_type['公告类型']

                # 获取相应的 id
                type_id = announcement_types[announcement_type]

                # 插入到 announcement_labels 表中
                insert_into_announcement_labels(cursor, title[0], type_id)
            except Exception as e:
                print(f"Error processing title {title[0]}: {e}, title is {title[1]}")
                # 在异常情况下，将类型标记为 "其他" 并插入数据库
                type_id = announcement_types['其他']
                insert_into_announcement_labels(cursor, title[0], type_id)
                continue

        # 在所有插入操作完成后提交事务
        db.commit()
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    tenderLabeling()