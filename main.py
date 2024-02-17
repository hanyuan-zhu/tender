from config import WEBPAGE_URL
from webdriver_util import init_driver, setup_search_conditions
from database_util import connect_db, check_existence, insert_data
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time

def crawl_data(driver):
    # 等待搜索结果更新
    old_record_count = driver.find_element(By.CSS_SELECTOR, "#search_topleft b").text
    driver.find_element(By.ID, "searchButton").click()
    wait = WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element(By.CSS_SELECTOR, "#search_topleft b").text != old_record_count)
    
    total_pages = int(driver.find_element(By.CSS_SELECTOR, ".paging .count").text.split(' ')[1])
    current_page = 1
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            while current_page <= total_pages:
                tenders = driver.find_elements(By.CSS_SELECTOR, '.publicont')
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
                
                if current_page < total_pages:
                    next_page_link = f"javascript:getList({current_page + 1})"
                    driver.execute_script(next_page_link)
                    current_page += 1
                    time.sleep(2)  # 等待页面加载，可根据实际情况调整
        finally:
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
    else:
        print("Failed to connect to the database.")

def main():
    driver = init_driver()
    try:
        setup_search_conditions(driver, WEBPAGE_URL)
        crawl_data(driver)
    finally:
        driver.quit()
        print("WebDriver session has ended.")

if __name__ == "__main__":
    main()
