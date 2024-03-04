from config import WEBPAGE_URL
from webdriverUtil import initDriver, setupSearchConditions
from crawlIndex import crawlIndex
from crawlDetail import fetchAndSaveDetailInfo
from cleanHtml import cleanAndUpdateHtml
from aiExtract import aiExtract


def main():
    driver = initDriver()
    try:
        setupSearchConditions(driver, WEBPAGE_URL)
        crawlIndex(driver)
    finally:
        driver.quit()
        print("WebDriver session has ended.")
        
    fetchAndSaveDetailInfo()
    cleanAndUpdateHtml()
    aiExtract()

if __name__ == "__main__":
    main()
