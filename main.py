import logging
from config import WEBPAGE_URL
from webdriverUtil import initDriver, setupSearchConditions
from crawlIndex import crawlIndex
from crawlDetail import fetchAndSaveDetailInfo
from cleanHtml import cleanAndUpdateHtml
from tender.aiExtractBackup import aiExtract
from tender.aiExtract import aiExtractBackup
from tenderLabeling import tenderLabeling
from reprocessAndUpdateOtherType import reprocessAndUpdateOtherType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    driver = None
    try:
        driver = initDriver()
        setupSearchConditions(driver, WEBPAGE_URL)
        crawlIndex(driver)
    except Exception as e:
        logging.error(f"An error occurred during web crawling: {e}")
    finally:
        if driver:
            driver.quit()
        logging.info("WebDriver session has ended.")
    
    # Each of these functions should have their own error handling as well.
    try:
        fetchAndSaveDetailInfo()
    except Exception as e:
        logging.error(f"Error fetching and saving detail info: {e}")
    
    try:
        cleanAndUpdateHtml()
    except Exception as e:
        logging.error(f"Error cleaning and updating HTML: {e}")
    
    try:
        tenderLabeling()
    except Exception as e:
        logging.error(f"Error Labeling: {e}")

    try:
        reprocessAndUpdateOtherType()
    except Exception as e:
        logging.error(f"Error reprocess other type: {e}")

    
    try:
        aiExtract()
    except Exception as e:
        logging.error(f"Error in AI extraction: {e}")
    
    try:
        aiExtractBackup()
    except Exception as e:
        logging.error(f"Error in AI backup extraction: {e}")

if __name__ == "__main__":
    main()
