from config import WEBPAGE_URL
from webdriver_util import init_driver, setup_search_conditions
from crawl_index import crawl_data
from crawl_detail import fetch_and_save_detail_info
from clean_html import clean_and_update_html


def main():
    driver = init_driver()
    try:
        setup_search_conditions(driver, WEBPAGE_URL)
        crawl_data(driver)
    finally:
        driver.quit()
        print("WebDriver session has ended.")
        
    fetch_and_save_detail_info()
    clean_and_update_html()

if __name__ == "__main__":
    main()
