from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from config import CHROMEDRIVER_PATH, HEADLESS



############################################################################################################
# 以下函数用于main.py：
# - initDriver (也用于 crawlDetail.py)
# - setupSearchConditions
############################################################################################################
def initDriver():
    service = Service(CHROMEDRIVER_PATH)
    options = Options()
    if HEADLESS:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')  # 绕过OS安全模型
    options.add_argument('--disable-dev-shm-usage')  # 解决资源限制问题
    options.add_argument('--disable-gpu')  # 禁用GPU加速，某些情况下有帮助

    driver = webdriver.Chrome(service=service, options=options)
    return driver

def setupSearchConditions(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.ID, "choose_time_04"))).click() # 04: 本月; 03：近十天; 02:近三天
    wait.until(EC.element_to_be_clickable((By.ID, "choose_source_1"))).click()
    Select(driver.find_element(By.ID, "provinceId")).select_by_value("440000")
    wait.until(EC.element_to_be_clickable((By.ID, "choose_classify_01"))).click()
    wait.until(EC.element_to_be_clickable((By.ID, "choose_stage_0101"))).click()
    driver.find_element(By.ID, "FINDTXT").send_keys("监理")
