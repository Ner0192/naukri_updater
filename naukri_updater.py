#! python3

import logging
import os
import sys
import time
import traceback
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Set true to run Chrome in headless mode for GitHub Actions
HEADLESS = True

# Set true to save logs in a file
FILELOGS = False

# Update your naukri credentials in GitHub Secrets
USERNAME = os.environ.get("NAUKRI_EMAIL")
PASSWORD = os.environ.get("NAUKRI_PASSWORD")

NaukriURL = "https://www.naukri.com/"


# ==========================================
# CUSTOM COLORED LOGGER SETUP
# ==========================================
class ColoredFormatter(logging.Formatter):
    """Custom Formatter to colorize specific parts of the log."""

    grey = "\x1b[90m"  # Light grey for timestamp
    cyan = "\x1b[36m"  # Cyan for INFO
    yellow = "\x1b[33m"  # Yellow for WARNING
    red = "\x1b[31m"  # Red for ERROR
    reset = "\x1b[0m"  # Reset to terminal default (usually white)

    def format(self, record):
        # Determine the color for the log level
        if record.levelno == logging.INFO:
            level_color = self.cyan
        elif record.levelno == logging.WARNING:
            level_color = self.yellow
        elif record.levelno >= logging.ERROR:
            level_color = self.red
        else:
            level_color = self.reset

        # Build the format string: Grey Time - Colored Level - White Message
        log_fmt = f"{self.grey}%(asctime)s{self.reset} - {level_color}%(levelname)s{self.reset} - %(message)s"

        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 1. Console Handler (with Colors)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)

# 2. File Handler (Clean Text, No Colors)
if FILELOGS:
    file_handler = logging.FileHandler("naukri.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

# Environment variables for WebDriverManager logs
os.environ["WDM_LOCAL"] = "1"
os.environ["WDM_LOG_LEVEL"] = "0"
# ==========================================


def catch(error):
    """Method to catch errors and log error details"""
    _, _, exc_tb = sys.exc_info()
    lineNo = str(exc_tb.tb_lineno) if exc_tb else "Unknown"
    msg = "%s : %s at Line %s.\n%s" % (
        type(error).__name__,
        error,
        lineNo,
        traceback.format_exc(),
    )
    logger.error(msg)


def getObj(locatorType):
    """This map defines how elements are identified"""
    map = {
        "ID": By.ID,
        "NAME": By.NAME,
        "XPATH": By.XPATH,
        "TAG": By.TAG_NAME,
        "CLASS": By.CLASS_NAME,
        "CSS": By.CSS_SELECTOR,
        "LINKTEXT": By.LINK_TEXT,
    }
    return map[locatorType.upper()]


def GetElement(driver, elementTag, locator="ID"):
    """Wait max 15 secs for element and then select when it is available"""
    try:

        def _get_element(_tag, _locator):
            _by = getObj(_locator)
            if is_element_present(driver, _by, _tag):
                return WebDriverWait(driver, 15).until(
                    lambda d: driver.find_element(_by, _tag)
                )

        element = _get_element(elementTag, locator.upper())
        if element:
            return element
        else:
            logger.warning("Element not found with %s : %s" % (locator, elementTag))
            return None
    except Exception as e:
        catch(e)
    return None


def is_element_present(driver, how, what):
    """Returns True if element is present"""
    try:
        driver.find_element(by=how, value=what)
    except NoSuchElementException:
        return False
    return True


def WaitTillElementPresent(driver, elementTag, locator="ID", timeout=30):
    """Wait till element present. Default 30 seconds"""
    result = False
    driver.implicitly_wait(0)
    locator = locator.upper()

    for _ in range(timeout):
        time.sleep(0.99)
        try:
            if is_element_present(driver, getObj(locator), elementTag):
                result = True
                break
        except Exception as e:
            pass

    if not result:
        logger.warning(
            "WaitTimeout: Element not found with %s : %s" % (locator, elementTag)
        )
    driver.implicitly_wait(3)
    return result


def ci(xpath_part: str) -> str:
    """Wraps an XPath string in lowercase translate() for case-insensitive matching."""
    return f"translate({xpath_part},'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"


def tearDown(driver):
    """Gracefully close and quit the driver"""
    try:
        driver.close()
        logger.info("Driver Closed Successfully")
    except Exception as e:
        pass

    try:
        driver.quit()
        logger.info("Driver Quit Successfully")
    except Exception as e:
        pass


def LoadNaukri(headless):
    """Open Chrome to load Naukri.com"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )
    except Exception as e:
        logger.error(f"Error launching Chrome: {e}")
        sys.exit(1)

    logger.info("Google Chrome Driver Launched!")
    driver.implicitly_wait(5)
    driver.get(NaukriURL)
    return driver


def naukriLogin(headless=False):
    """Open Chrome browser and Login to Naukri.com"""
    status = False
    driver = None
    login_layer_id = "login_Layer"
    username_locator = (
        "//input[contains(@placeholder, 'Email') or contains(@placeholder, 'Username')]"
    )
    password_locator = "//input[contains(@placeholder, 'password') or @type='password']"
    login_btn_locator = "//button[contains(text(), 'Login')]"
    chatbot_cross = (
        "//*[contains(@class, 'crossIcon') or contains(@class, 'chatbot_Cross')]"
    )

    try:
        driver = LoadNaukri(headless)
        time.sleep(2)

        if WaitTillElementPresent(driver, login_layer_id, "ID", 10):
            GetElement(driver, login_layer_id, "ID").click()
            time.sleep(1)

        logger.info("Entering credentials...")
        emailFieldElement = GetElement(driver, username_locator, "XPATH")
        passFieldElement = GetElement(driver, password_locator, "XPATH")
        loginButton = GetElement(driver, login_btn_locator, "XPATH")

        if emailFieldElement and passFieldElement and loginButton:
            emailFieldElement.clear()
            for char in USERNAME:
                emailFieldElement.send_keys(char)
                time.sleep(0.01)
            time.sleep(1)

            passFieldElement.clear()
            for char in PASSWORD:
                passFieldElement.send_keys(char)
                time.sleep(0.01)
            time.sleep(1)

            loginButton.click()
            time.sleep(5)

            # Check for Chatbot and skip
            if is_element_present(driver, By.XPATH, chatbot_cross):
                try:
                    GetElement(driver, chatbot_cross, "XPATH").click()
                    logger.info("Chatbot closed.")
                    time.sleep(1)
                except:
                    pass

            status = True
            logger.info("Naukri Login Sequence Executed.")
        else:
            logger.error("Could not find login elements.")

    except Exception as e:
        catch(e)

    return (status, driver)


def UpdateProfileSummary(driver):
    """Navigates to Profile and appends/removes a dot at the end of the summary."""
    try:
        logger.info("Navigating to Profile...")
        driver.get("https://www.naukri.com/mnjuser/profile")

        WaitTillElementPresent(driver, "//body", locator="XPATH", timeout=20)
        time.sleep(3)

        # 1. The lazy-load container is in the DOM immediately, but its content
        #    only renders once scrolled into view. Find it by ID first.
        lazy_id = "lazyProfileSummary"
        if not WaitTillElementPresent(driver, lazy_id, "ID", 15):
            logger.error("lazyProfileSummary container not found on page.")
            return

        # 2. Scroll the container into view to trigger lazy loading.
        logger.info("Scrolling to Profile Summary section to trigger lazy load...")
        lazy_el = GetElement(driver, lazy_id, "ID")
        if lazy_el:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", lazy_el
            )
            time.sleep(2)  # wait for the lazy-load JS to render the content

        # 3. Now wait for the widgetTitle span to appear inside that section.
        #    Anchoring to the section ID avoids false matches in the sidebar/other cards.
        summary_xpath = (
            "//div[@id='lazyProfileSummary']" "//span[contains(@class, 'widgetTitle')]"
        )

        if not WaitTillElementPresent(driver, summary_xpath, "XPATH", 15):
            logger.error("Profile Summary widgetTitle not found after scrolling.")
            return

        logger.info("Profile Summary section found.")
        summary_header = GetElement(driver, summary_xpath, locator="XPATH")
        if summary_header:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", summary_header
            )
            time.sleep(1)

        # 4. Edit button is a following-sibling of the widgetTitle span.
        #    Still anchored to the section ID to be unambiguous.
        edit_locator = (
            "//div[@id='lazyProfileSummary']"
            "//span[contains(@class, 'widgetTitle')]"
            "/following-sibling::span[contains(@class, 'edit')]"
        )

        if not WaitTillElementPresent(driver, edit_locator, "XPATH", 10):
            logger.error("Edit button for Profile Summary not found.")
            return

        edit_btn = GetElement(driver, edit_locator, locator="XPATH")
        driver.execute_script("arguments[0].click();", edit_btn)
        time.sleep(2)

        # 5. Modify the text inside the drawer textarea.
        text_area = GetElement(driver, "profileSummaryTxt", locator="ID")
        if text_area:
            current_text = text_area.get_attribute("value")

            if current_text and current_text.endswith("."):
                new_text = current_text[:-1]
            else:
                new_text = (current_text or "") + "."

            text_area.send_keys(Keys.CONTROL + "a")
            time.sleep(0.5)
            text_area.send_keys(Keys.DELETE)
            time.sleep(0.5)
            text_area.send_keys(new_text)
            time.sleep(1)

            # 6. Save
            save_btn_xpath = (
                "//form[@name='profileSummaryForm']"
                "//button[@type='submit' and text()='Save']"
            )
            save_btn = GetElement(driver, save_btn_xpath, locator="XPATH")
            if save_btn:
                driver.execute_script("arguments[0].click();", save_btn)
                logger.info(
                    f"Profile updated successfully. New length: {len(new_text)}"
                )
                time.sleep(3)
            else:
                logger.error("Save button not found.")
        else:
            logger.error("Profile Summary textarea not found.")

    except Exception as e:
        catch(e)


def Logout(driver):
    """Logout from Naukri session using specific Drawer & Logout link XPaths"""
    try:
        # -------- Drawer Menu XPaths --------
        drawer_xpaths = [
            f"//div[contains({ci('@class')}, 'nI-gNb-drawer')]",
            f"//*[contains({ci('@class')}, 'drawer__icon')]",
            f"//img[contains({ci('@alt')}, 'profile')]",
            f"//div[contains({ci('@class')}, 'info__view-profile')]",
        ]

        drawer_opened = False
        for xpath in drawer_xpaths:
            if is_element_present(driver, By.XPATH, xpath):
                try:
                    el = GetElement(driver, xpath, locator="XPATH")
                    if el:
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(2)
                        logger.info(f"Drawer menu opened using {xpath}")
                        drawer_opened = True
                        break
                except Exception as e:
                    continue

        if not drawer_opened:
            logger.warning("Could not open profile drawer menu.")

        # -------- Logout XPaths --------
        logout_xpaths = [
            f"//a[contains({ci('@href')}, 'logout')]",
            f"//a[.//i[contains({ci('@class')}, 'ni-gnb-icn-logout')]]",
            "//a[@data-type='logoutLink']",
            f"//a[contains({ci('@class')}, 'logout')]",
            f"//a[contains({ci('@title')}, 'logout')]",
            f"//*[contains({ci('text()')}, 'logout')]",
        ]

        for xpath in logout_xpaths:
            if is_element_present(driver, By.XPATH, xpath):
                try:
                    el = GetElement(driver, xpath, locator="XPATH")
                    if el:
                        driver.execute_script("arguments[0].scrollIntoView(true);", el)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(2)
                        logger.info("Logout Successful")
                        return True
                except Exception as e:
                    continue

        logger.warning("Logout button not found via UI. Clearing Cookies.")
        driver.delete_all_cookies()
        return False

    except Exception as e:
        catch(e)
        return False


def main():
    logger.info("Naukri Profile Updater Script Begin")
    driver = None

    if not USERNAME or not PASSWORD:
        logger.error(
            "ERROR: NAUKRI_EMAIL or NAUKRI_PASSWORD environment variables not set."
        )
        sys.exit(1)

    try:
        status, driver = naukriLogin(HEADLESS)
        if status:
            UpdateProfileSummary(driver)

    except Exception as e:
        catch(e)

    finally:
        if driver is not None:
            try:
                Logout(driver)
                time.sleep(2)
            except Exception as e:
                logger.error("Error during logout: %s" % e)
        tearDown(driver)

    logger.info("Naukri Profile Updater Script Ended\n")


if __name__ == "__main__":
    main()
