from database_util import connect_db, check_existence, insert_data
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from selenium.common.exceptions import TimeoutException

def crawl_data(driver):
    # 等待搜索结果更新
    old_record_count = driver.find_element(By.CSS_SELECTOR, "#search_topleft b").text
    driver.find_element(By.ID, "searchButton").click()
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element(By.CSS_SELECTOR, "#search_topleft b").text != old_record_count)
    
    total_pages_elements = driver.find_elements(By.CSS_SELECTOR, ".paging .count")
    # 注意：这里我们假设总页数总是在最后一个 ".paging .count" 元素中。
    # 如果网页结构改变，这可能不再成立，需要重新检查和调整这部分代码。
    total_pages = int(total_pages_elements[-1].text.split(' ')[1])    
    current_page = 1
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            while current_page <= total_pages:
                tenders = driver.find_elements(By.CSS_SELECTOR, '.publicont')
                print(f"Page {current_page} has {len(tenders)} tenders.")
                
                page_has_existing_data = False
                
                for tender in tenders:
                    detail_link = tender.find_element(By.CSS_SELECTOR, 'h4 a').get_attribute('href')
                    if check_existence(cursor, detail_link):
                        page_has_existing_data = True
                        print(f"Tender already exists in database: {detail_link}")
                    else:
                        title = tender.find_element(By.CSS_SELECTOR, 'h4 a').text
                        publish_time_str = tender.find_element(By.CSS_SELECTOR, '.span_o').text
                        try:
                            publish_time = datetime.strptime(publish_time_str, '%Y-%m-%d').date()
                        except ValueError as e:
                            print(f"Error parsing date: {e}")
                            publish_time = None
                        province = tender.find_elements(By.CSS_SELECTOR, '.p_tw .span_on')[0].text
                        source_platform = tender.find_elements(By.CSS_SELECTOR, '.p_tw .span_on')[1].text
                        business_type = tender.find_elements(By.CSS_SELECTOR, '.p_tw .span_on')[2].text
                        info_type = tender.find_elements(By.CSS_SELECTOR, '.p_tw .span_on')[3].text
                        industry = tender.find_elements(By.CSS_SELECTOR, '.p_tw .span_on')[4].text if len(tender.find_elements(By.CSS_SELECTOR, '.p_tw .span_on')) > 4 else 'N/A'
                        
                        insert_data(cursor, (title, publish_time, province, source_platform, business_type, info_type, industry, detail_link))
                        connection.commit()
                
                if page_has_existing_data:
                    print("Existing data found on current page, stopping.")
                    break
                
                current_page += 1
                print(f"Moving to page {current_page}...")
                if current_page > total_pages:
                    break

                next_page_link = f"javascript:getList({current_page})"
                driver.execute_script(next_page_link)
                try:
                    # 注意：这里我们假设页面加载成功时，对应的链接元素会包含 "a_hover" 类。
                    # 如果网页结构改变，这可能不再成立，需要重新检查和调整这部分代码。
                    WebDriverWait(driver, 10).until(lambda driver: "a_hover" in driver.find_element(By.CSS_SELECTOR, f'a[href="{next_page_link}"]').get_attribute("class"))
                    print("Page loaded successfully.")
                except TimeoutException:
                    print("Timeout while waiting for page to load.")
        finally:
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
    else:
        print("Failed to connect to the database.")



if __name__ == "__main__":
    crawl_data()
