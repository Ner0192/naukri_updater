#! python3

import logging
import os
import sys
import time
import traceback
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

HEADLESS = True
FILELOGS = False

USERNAME = os.environ.get("NAUKRI_EMAIL")
PASSWORD = os.environ.get("NAUKRI_PASSWORD")

NaukriURL = "https://www.naukri.com/"


# ==========================================
# CUSTOM COLORED LOGGER SETUP
# ==========================================
class ColoredFormatter(logging.Formatter):
    grey = "\x1b[90m"
    cyan = "\x1b[36m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    reset = "\x1b[0m"

    def format(self, record):
        if record.levelno == logging.INFO:
            level_color = self.cyan
        elif record.levelno == logging.WARNING:
            level_color = self.yellow
        elif record.levelno >= logging.ERROR:
            level_color = self.red
        else:
            level_color = self.reset

        log_fmt = (
            f"{self.grey}%(asctime)s{self.reset} - "
            f"{level_color}%(levelname)s{self.reset} - %(message)s"
        )
        return logging.Formatter(log_fmt).format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)

if FILELOGS:
    file_handler = logging.FileHandler("naukri.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

os.environ["WDM_LOCAL"] = "1"
os.environ["WDM_LOG_LEVEL"] = "0"
# ==========================================


def catch(error):
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


def is_element_present(driver, how, what):
    try:
        driver.find_element(by=how, value=what)
    except NoSuchElementException:
        return False
    return True


def ci(xpath_part: str) -> str:
    return (
        f"translate({xpath_part},"
        f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
    )


def saveDebugScreenshot(driver, name="debug"):
    """Save a timestamped screenshot for headless debugging."""
    try:
        filename = f"{name}_{int(time.time())}.png"
        driver.save_screenshot(filename)
        logger.info(f"Screenshot saved → {filename}")
    except Exception as e:
        logger.warning(f"Could not save screenshot: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CORE WAIT HELPER  ← the main fix
# ─────────────────────────────────────────────────────────────────────────────
def waitForElement(driver, locator_type, locator, timeout=30, condition="clickable"):
    """
    Block until an element satisfies `condition`, then return it.

    condition options:
      'present'   – element exists anywhere in the DOM (even if hidden/skeleton)
      'visible'   – element is in the DOM AND visible (non-zero size, not hidden)
      'clickable' – element is visible AND enabled (fully rendered, not a skeleton)

    Always use 'clickable' for anything you intend to interact with.
    Use 'visible' for read-only elements you just want to read.
    Only use 'present' as a last resort.

    Returns the element on success, None on timeout.
    """
    by = getObj(locator_type)
    locator_tuple = (by, locator)

    ec_map = {
        "present": EC.presence_of_element_located(locator_tuple),
        "visible": EC.visibility_of_element_located(locator_tuple),
        "clickable": EC.element_to_be_clickable(locator_tuple),
    }

    try:
        element = WebDriverWait(driver, timeout).until(ec_map[condition])
        logger.info(f"[✓] {condition} — {locator_type}: {locator}")
        return element
    except TimeoutException:
        logger.warning(
            f"[✗] Timeout ({timeout}s) waiting for {condition} element  "
            f"{locator_type}: {locator}"
        )
        saveDebugScreenshot(driver, f"timeout_{name_slug(locator)}")
        return None
    except Exception as e:
        catch(e)
        return None


def name_slug(s, max_len=30):
    """Turn an XPath into a short safe filename fragment."""
    return "".join(c if c.isalnum() else "_" for c in s)[:max_len]


# ─────────────────────────────────────────────────────────────────────────────


def waitForPageLoad(driver, timeout=30):
    """Wait for document.readyState == 'complete' before proceeding."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.info("Page readyState = complete.")
    except Exception:
        logger.warning("waitForPageLoad timed out — continuing anyway.")


def tearDown(driver):
    try:
        driver.close()
        logger.info("Driver Closed Successfully")
    except Exception:
        pass
    try:
        driver.quit()
        logger.info("Driver Quit Successfully")
    except Exception:
        pass


def LoadNaukri(headless):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )
    except Exception as e:
        logger.error(f"Error launching Chrome: {e}")
        sys.exit(1)

    logger.info("Google Chrome Driver Launched!")
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(0)  # disable implicit wait; we use explicit waits
    driver.get(NaukriURL)
    waitForPageLoad(driver)
    return driver


def verifyLogin(driver):
    """Confirm login actually succeeded by checking URL and authenticated DOM elements."""
    logger.info("Verifying login...")
    current_url = driver.current_url.lower()
    logger.info(f"Post-login URL   : {driver.current_url}")
    logger.info(f"Post-login title : {driver.title}")

    if "login" in current_url or "signup" in current_url:
        logger.error("Login FAILED — still on login/signup page.")
        saveDebugScreenshot(driver, "login_failed")
        return False

    auth_xpaths = [
        "//*[contains(@class,'nI-gNb-drawer')]",
        "//*[contains(@class,'view-profile')]",
        "//a[contains(@href,'mnjuser/profile')]",
    ]
    for xpath in auth_xpaths:
        if is_element_present(driver, By.XPATH, xpath):
            logger.info("Login verified via authenticated nav element.")
            return True

    if "naukri.com" in current_url:
        logger.warning("Login status uncertain — proceeding optimistically.")
        saveDebugScreenshot(driver, "login_uncertain")
        return True

    logger.error("Login verification failed.")
    saveDebugScreenshot(driver, "login_unverified")
    return False


def naukriLogin(headless=False):
    """Login to Naukri, waiting for every element to be truly clickable before use."""
    status = False
    driver = None

    # Possible XPaths for the nav-bar login trigger (the element that opens the modal)
    nav_login_xpaths = [
        "//*[@id='login_Layer']",
        "//a[contains(@href,'login') and not(contains(@href,'logout'))]",
        f"//a[contains({ci('text()')},'login')]",
        f"//button[contains({ci('text()')},'login')]",
    ]

    username_locator = "//input[contains(@placeholder,'Email') or contains(@placeholder,'email') or contains(@placeholder,'Username')]"
    password_locator = "//input[@type='password' or contains(@placeholder,'assword')]"
    login_btn_locator = "//button[@type='submit'] | //button[contains(text(),'Login')]"
    chatbot_cross = (
        "//*[contains(@class,'crossIcon') or contains(@class,'chatbot_Cross')]"
    )

    try:
        driver = LoadNaukri(headless)
        saveDebugScreenshot(driver, "00_homepage_loaded")

        # ── Step 1: wait for nav to exit skeleton, then click the login trigger ──
        logger.info(
            "Waiting for login trigger to be clickable (nav out of skeleton)..."
        )
        login_trigger = None
        for xpath in nav_login_xpaths:
            login_trigger = waitForElement(
                driver, "XPATH", xpath, timeout=30, condition="clickable"
            )
            if login_trigger:
                break

        if login_trigger:
            driver.execute_script("arguments[0].click();", login_trigger)
            logger.info("Login trigger clicked.")
            time.sleep(1)
        else:
            logger.warning("Login trigger not found — modal may open automatically.")
            saveDebugScreenshot(driver, "01_login_trigger_not_found")

        # ── Step 2: wait for the login form fields to be visible ─────────────
        logger.info("Waiting for login form fields...")
        emailField = waitForElement(
            driver, "XPATH", username_locator, timeout=20, condition="visible"
        )
        passField = waitForElement(
            driver, "XPATH", password_locator, timeout=10, condition="visible"
        )
        loginButton = waitForElement(
            driver, "XPATH", login_btn_locator, timeout=10, condition="clickable"
        )

        if not (emailField and passField and loginButton):
            logger.error("Login form elements not found after waiting.")
            saveDebugScreenshot(driver, "02_login_form_not_found")
            return (False, driver)

        # ── Step 3: fill and submit ───────────────────────────────────────────
        logger.info("Entering credentials...")
        emailField.clear()
        for char in USERNAME:
            emailField.send_keys(char)
            time.sleep(0.01)
        time.sleep(0.5)

        passField.clear()
        for char in PASSWORD:
            passField.send_keys(char)
            time.sleep(0.01)
        time.sleep(0.5)

        driver.execute_script("arguments[0].click();", loginButton)

        if not verifyLogin(driver):
            return (False, driver)

        # Close chatbot popup if it appears
        chatbot = waitForElement(
            driver, "XPATH", chatbot_cross, timeout=5, condition="clickable"
        )
        if chatbot:
            try:
                chatbot.click()
                logger.info("Chatbot closed.")
            except Exception:
                pass

        status = True
        logger.info("Naukri Login Successful.")

    except Exception as e:
        catch(e)

    return (status, driver)


def UpdateProfileSummary(driver):
    """
    Navigate to the profile page and toggle a trailing dot in the Profile Summary.
    Every interaction waits for the target element to be truly clickable first.
    """
    try:
        logger.info("Navigating to Profile...")
        driver.get("https://www.naukri.com/mnjuser/profile")
        waitForPageLoad(driver)
        saveDebugScreenshot(driver, "03_profile_loaded")

        logger.info(f"Profile URL   : {driver.current_url}")
        logger.info(f"Profile title : {driver.title}")

        # ── Incremental scroll to trigger every lazy-loaded section ───────────
        logger.info("Scrolling page to trigger lazy loading...")
        total_height = driver.execute_script("return document.body.scrollHeight")
        for pos in range(0, total_height + 600, 350):
            driver.execute_script(f"window.scrollTo(0, {pos});")
            time.sleep(0.25)
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        saveDebugScreenshot(driver, "04_after_scroll")

        # ── Wait for the edit button to be CLICKABLE (not just present) ───────
        edit_xpaths = [
            # Original (pre-2025 layout)
            "//div[@id='lazyProfileSummary']//span[contains(@class,'widgetTitle')]"
            "/following-sibling::span[contains(@class,'edit')]",
            # ID changed but still contains 'Summary'
            "//*[contains(@id,'Summary') or contains(@id,'summary')]//span[contains(@class,'edit')]",
            # Anchor on visible heading text
            "//*[contains(text(),'Profile Summary')]/following-sibling::*[contains(@class,'edit')]",
            "//*[contains(text(),'Profile Summary')]/..//*[contains(@class,'edit')]",
            # Generic fallback
            "//span[contains(@class,'edit') and ancestor::*[contains(@class,'summary') or contains(@id,'summary')]]",
        ]

        edit_btn = None
        for xpath in edit_xpaths:
            edit_btn = waitForElement(
                driver, "XPATH", xpath, timeout=15, condition="clickable"
            )
            if edit_btn:
                break

        if not edit_btn:
            logger.error("Profile Summary edit button not found / not clickable.")
            saveDebugScreenshot(driver, "05_edit_not_found")
            src = driver.page_source
            logger.info(f"Page source snippet:\n{src[:5000]}")
            return

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", edit_btn
        )
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", edit_btn)

        # ── Wait for the drawer/modal textarea to be visible ──────────────────
        textarea_specs = [
            ("ID", "profileSummaryTxt"),
            ("XPATH", "//textarea[contains(@id,'profileSummary')]"),
            ("XPATH", "//textarea[contains(@id,'Summary')]"),
            ("XPATH", "//textarea[contains(@name,'summary')]"),
            (
                "XPATH",
                "//form[contains(@name,'profileSummary') or contains(@name,'Summary')]//textarea",
            ),
        ]
        text_area = None
        for lt, loc in textarea_specs:
            text_area = waitForElement(driver, lt, loc, timeout=15, condition="visible")
            if text_area:
                break

        if not text_area:
            logger.error("Profile Summary textarea not found.")
            saveDebugScreenshot(driver, "06_textarea_not_found")
            return

        current_text = text_area.get_attribute("value") or ""
        logger.info(f"Current summary length: {len(current_text)}")
        new_text = (
            current_text[:-1] if current_text.endswith(".") else current_text + "."
        )

        text_area.send_keys(Keys.CONTROL + "a")
        time.sleep(0.3)
        text_area.send_keys(Keys.DELETE)
        time.sleep(0.3)
        text_area.send_keys(new_text)

        # ── Wait for the Save button to be clickable ──────────────────────────
        save_xpaths = [
            "//form[@name='profileSummaryForm']//button[@type='submit' and text()='Save']",
            "//button[@type='submit' and contains(text(),'Save')]",
            "//button[text()='Save']",
        ]
        save_btn = None
        for xpath in save_xpaths:
            save_btn = waitForElement(
                driver, "XPATH", xpath, timeout=10, condition="clickable"
            )
            if save_btn:
                break

        if save_btn:
            driver.execute_script("arguments[0].click();", save_btn)
            logger.info(f"Profile updated ✓  New length: {len(new_text)}")
            time.sleep(3)
        else:
            logger.error("Save button not found.")
            saveDebugScreenshot(driver, "07_save_not_found")

    except Exception as e:
        catch(e)
        saveDebugScreenshot(driver, "99_exception")


def Logout(driver):
    try:
        drawer_xpaths = [
            f"//div[contains({ci('@class')},'nI-gNb-drawer')]",
            f"//*[contains({ci('@class')},'drawer__icon')]",
            f"//img[contains({ci('@alt')},'profile')]",
            f"//div[contains({ci('@class')},'info__view-profile')]",
        ]
        for xpath in drawer_xpaths:
            el = waitForElement(
                driver, "XPATH", xpath, timeout=5, condition="clickable"
            )
            if el:
                driver.execute_script("arguments[0].click();", el)
                logger.info(f"Drawer opened: {xpath}")
                time.sleep(2)
                break
        else:
            logger.warning("Could not open profile drawer menu.")

        logout_xpaths = [
            f"//a[contains({ci('@href')},'logout')]",
            f"//a[.//i[contains({ci('@class')},'ni-gnb-icn-logout')]]",
            "//a[@data-type='logoutLink']",
            f"//a[contains({ci('@class')},'logout')]",
            f"//*[contains({ci('text()')},'logout')]",
        ]
        for xpath in logout_xpaths:
            el = waitForElement(
                driver, "XPATH", xpath, timeout=5, condition="clickable"
            )
            if el:
                driver.execute_script("arguments[0].scrollIntoView(true);", el)
                driver.execute_script("arguments[0].click();", el)
                logger.info("Logout Successful")
                return True

        logger.warning("Logout button not found — clearing cookies.")
        driver.delete_all_cookies()
        return False

    except Exception as e:
        catch(e)
        return False


def main():
    logger.info("Naukri Profile Updater Script Begin")
    driver = None

    if not USERNAME or not PASSWORD:
        logger.error("NAUKRI_EMAIL or NAUKRI_PASSWORD environment variables not set.")
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
                logger.error(f"Error during logout: {e}")
        tearDown(driver)

    logger.info("Naukri Profile Updater Script Ended\n")


if __name__ == "__main__":
    main()
