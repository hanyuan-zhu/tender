from database_util import connect_db,get_unfetched_tender_info,insert_detail_html,update_fetched_status
from webdriverUtil import initDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re



def fetchAndSaveDetailInfo():
    print("Connecting to database...")
    connection = connect_db()
    cursor = connection.cursor()

    print("Fetching tenders from database...")
    tenders = get_unfetched_tender_info(cursor)

    for tender in tenders:
        tender_id, detail_link = tender
        print(f"Processing tender {tender_id}...")
        
        print("Initializing web driver...")
        driver = initDriver()
        driver.get(detail_link)

        max_attempts = 3  # 最大尝试次数
        attempts = 0  # 当前尝试次数

        while attempts < max_attempts:
            try:
                # 尝试加载iframe
                print("Waiting for iframe to load...")
                iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "iframe0101")))
                driver.switch_to.frame(iframe)
                # 如果成功加载，跳出循环
                break
            except TimeoutException:
                # 如果加载失败，增加尝试次数，可选择刷新页面或其他恢复操作
                attempts += 1
                driver.refresh()  # 可选：刷新页面尝试重新加载

        if attempts == max_attempts:
            print("Failed to load iframe after maximum attempts.")
            # 处理最大尝试次数后仍未成功加载的情况
        else:
            print("Fetching data...") 
            html_content = driver.page_source  # 获取当前iframe的页面源代码
            
            # 假设html_content包含了您从iframe获取的HTML内容
            soup = BeautifulSoup(html_content, 'html.parser')

            title = soup.find('h4', class_='h4_o').get_text()

            publish_time_text = soup.find('p', class_='p_o').get_text()
            publish_time_match = re.search(r'发布时间：([\d\-\:\s]+)', publish_time_text)
            publish_time = publish_time_match.group(1) if publish_time_match else "未找到发布时间"

            # 使用正则表达式查找包含“原文链接地址”的<a>标签
            html_str = str(html_content)
            match = re.search(r'<a target="_blank" href="(.*?)">原文链接地址</a>', html_str)
            if match:
                original_link = match.group(1)
            else:
                original_link = "未找到原文链接"

            # 定位到<div class="detail_content">
            detail_content_div = soup.find('div', class_='detail_content')
            # 提取并拼接内部HTML内容
            original_detail_html = ''.join([str(item) for item in detail_content_div.contents])


            print("Inserting data into database...")
            # 假设 insert_detail_html 是一个已定义的函数，用于将数据插入数据库
            insert_detail_html(cursor, (tender_id, title, publish_time, original_link, original_detail_html))
            connection.commit()

            print("Updating fetched status...")
            # 假设 update_fetched_status 是一个已定义的函数，用于更新抓取状态
            update_fetched_status(cursor, tender_id)
            connection.commit()

            print("Cleaning up...")
            driver.switch_to.default_content()
        driver.quit()

    print("Closing database connection...")
    cursor.close()
    connection.close()

if __name__ == "__main__":
    fetchAndSaveDetailInfo()