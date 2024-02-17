from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from config import CHROMEDRIVER_PATH, HEADLESS

def init_driver():
    service = Service(CHROMEDRIVER_PATH)
    options = Options()
    if HEADLESS:
        options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def setup_search_conditions(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.ID, "choose_time_03"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "choose_source_1"))).click()
    Select(driver.find_element(By.ID, "provinceId")).select_by_value("440000")
    wait.until(EC.element_to_be_clickable((By.ID, "choose_classify_01"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "choose_stage_0101"))).click()
    driver.find_element(By.ID, "FINDTXT").send_keys("监理")
