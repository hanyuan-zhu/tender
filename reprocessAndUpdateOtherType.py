# Description: 重新处理数据库中类型为 "其他" 的标题，并更新数据库

import json
from tenderLabeling import tender_categorization
from database_util import connect_db, get_announcement_types

def get_titles_with_other_type(cursor):
    # 从数据库中获取类型为 "其他" 的标题
    cursor.execute("""
        SELECT a.tender_id, t.title 
        FROM announcement_labels AS a
        JOIN tender_index AS t ON a.tender_id = t.id
        WHERE a.type_id = (SELECT id FROM announcement_catalog WHERE announcement_type = '其他')
    """)
    return cursor.fetchall()

def reprocess_and_update_titles(cursor, db, titles, announcement_catalog):
    for title in titles:
        try:
            # 重新处理标题
            type_temp = tender_categorization(title[1])
            tender_title_type = json.loads(type_temp.replace("'", "\""))
            announcement_type = tender_title_type['公告类型']

            # 如果类型不再是 "其他"，则更新数据库
            if announcement_type != '其他':
                type_id = announcement_catalog[announcement_type]
                print(f"type_id: {type_id}, title[0]: {title[0]}")  # 打印 type_id 和 title[0] 的值
                cursor.execute("UPDATE announcement_labels SET type_id = %s WHERE tender_id = %s", (type_id, title[0]))
                print(f"Title '{title[1]}' was updated. New type is '{announcement_type}'")
            else:
                print(f"Title '{title[1]}' was not updated. Type remains '其他'")
        except Exception as e:
            print(f"Error reprocessing title {title[0]}: {e}, title is {title[1]}")
            continue

    # 在所有更新操作完成后提交事务
    db.commit()
    
    
def reprocessAndUpdateOtherType():
    db=connect_db()
    cursor=db.cursor()
    try:
        announcement_types = get_announcement_types(cursor)

        # 使用 get_titles_with_other_type 函数获取类型为 "其他" 的标题
        titles_with_other_type = get_titles_with_other_type(cursor)

        # 使用 reprocess_and_update_titles 函数重新处理这些标题并更新数据库
        reprocess_and_update_titles(cursor, db, titles_with_other_type, announcement_types)
        
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    reprocessAndUpdateOtherType()