import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

#path
webdriver_path = '/home/deezsec/Downloads/geckodriver'
credentials_file = 'active_facebook_credentials.txt'

def log_status(message):
    print(f"\033[97m[ASTRA] {message}\033[0m")  #white text

WHITE = "\033[97m"
RESET = "\033[0m"

def get_credentials():
    if os.path.exists(credentials_file):
        log_status("Using saved credentials from previous session.")
        with open(credentials_file, 'r') as file:
            credentials = file.read().splitlines()
            if len(credentials) == 2:
                return credentials[0], credentials[1]
    else:
        username = input("Enter your Facebook email: ")
        password = input("Enter your Facebook password: ")
        with open(credentials_file, 'w') as file:
            file.write(f"{username}\n{password}")
        log_status("Credentials saved for future use.")
        return username, password

def initialize_webdriver():
    firefox_options = Options()
    firefox_options.set_preference("dom.webnotifications.enabled", False)
    firefox_options.set_preference("media.volume_scale", "0.0")
    firefox_options.set_preference("privacy.trackingprotection.enabled", True)

    try:
        driver = webdriver.Firefox(service=Service(webdriver_path), options=firefox_options)
        log_status("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        log_status(f"Error initializing WebDriver: {e}")
        raise

def login_facebook(driver, username, password):
    try:
        log_status("Navigating to Facebook login page...")
        driver.get("https://www.facebook.com/login")

        log_status("Attempting to find email and password fields...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_field = driver.find_element(By.NAME, "email")
        email_field.send_keys(username)

        password_field = driver.find_element(By.NAME, "pass")
        password_field.send_keys(password)
        log_status("Credentials entered.")

        log_status("Submitting login form...")
        password_field.send_keys(Keys.RETURN)
        verification_prompt = input(WHITE + "Do you see any 'Suspicious Login/2FA' page? (yes/no): ").strip().lower()
        if verification_prompt == "yes":
            log_status(WHITE + "Waiting for input from user...")
            input(WHITE + "Press Enter once the Verification is completed...")

        log_status("Waiting for login to complete...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label, 'Your profile')]"))
        )
        log_status("Successfully logged in.")
    except Exception as e:
        log_status(f"Error during login: {e}")
        raise

def check_profile_privacy(driver):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@role='banner']")))
        log_status("Profile is public.")
        return True
    except NoSuchElementException:
        log_status("Profile might be private or unavailable.")
        return False


def scroll_and_screenshot(driver, section_name, folder_name, max_scrolls=5):
    screenshot_paths = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0

    while scroll_count < max_scrolls:
        try:
            log_status(f"Taking screenshot for {section_name}, scroll {scroll_count + 1}...")
            screenshot_path = os.path.join(folder_name, f'{section_name}_{int(time.time())}.png')
            driver.save_screenshot(screenshot_path)
            screenshot_paths.append(screenshot_path)
            log_status(f"Screenshot saved at {screenshot_path}")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  #wait for the content to load

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                log_status(f"No more content to scroll in {section_name}. Ending scroll.")
                break
            last_height = new_height
            scroll_count += 1
        except StaleElementReferenceException:
            log_status("Encountered stale element. Retrying...")
            time.sleep(2)  #wait before retrying
            last_height = driver.execute_script("return document.body.scrollHeight")

    return screenshot_paths

def click_see_all(driver, section):
    try:
        see_all_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[text()='See all {section}']"))
        )
        see_all_button.click()
        log_status(f"Clicked 'See All' for {section} section.")
        time.sleep(3)  # Wait for the page to load
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
        log_status(f"Could not find or click 'See All' button for {section}: {e}")

def save_pdf_report(folder_name, profile_screenshots, target_username):
    pdf_path = os.path.join(folder_name, f'{target_username}_report.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y_position = height - 50 

    def draw_image_with_text(img_path, description):
        nonlocal y_position
        if y_position < 100:
            c.showPage()
            y_position = height - 50
        c.drawString(50, y_position, description)
        y_position -= 20  #add some gap
        c.drawImage(img_path, 50, y_position - 300, width=500, height=300)
        y_position -= 310

    for img_path in profile_screenshots:
        section_name = os.path.basename(img_path).split('_')[0]
        description = f"Screenshot of {target_username}'s {section_name} section"
        draw_image_with_text(img_path, description)

    c.save()
    log_status(f"PDF report saved at {pdf_path}")

def scrape_profile_info(driver, target_username):
    folder_name = f"{target_username}_facebook"
    os.makedirs(folder_name, exist_ok=True)
    profile_screenshots = []

    try:
        log_status(f"Navigating to {target_username}'s profile...")
        driver.get(f"https://www.facebook.com/{target_username}")

        if not check_profile_privacy(driver):
            return

        profile_screenshots.extend(scroll_and_screenshot(driver, 'profile_homepage', folder_name))

        sections = ['about', 'photos', 'videos', 'friends', 'posts']
        for section in sections:
            log_status(f"Navigating to {section} section...")
            driver.get(f"https://www.facebook.com/{target_username}/{section}")

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(5)  # Wait for all elements to load

            if section == 'videos':
                click_see_all(driver, 'videos')
                profile_screenshots.extend(scroll_and_screenshot(driver, section, folder_name, max_scrolls=3))
            elif section == 'posts':
                profile_screenshots.extend(scroll_and_screenshot(driver, section, folder_name, max_scrolls=10))
            elif section == 'friends':
                click_see_all(driver, 'friends')
                profile_screenshots.extend(scroll_and_screenshot(driver, section, folder_name, max_scrolls=2))
            else:
                profile_screenshots.extend(scroll_and_screenshot(driver, section, folder_name))

        #save the PDF
        save_pdf_report(folder_name, profile_screenshots, target_username)

        log_status("Profile information scraped and saved successfully.")
    except Exception as e:
        log_status(f"Error scraping profile information: {e}")
        error_screenshot_path = os.path.join(folder_name, 'scrape_error.png')
        driver.save_screenshot(error_screenshot_path)
        log_status(f"Error screenshot saved at {error_screenshot_path}")

def main():
    username, password = get_credentials()
    driver = initialize_webdriver()

    try:
        login_facebook(driver, username, password)

        target_username = input(WHITE + "Enter the target username: ").strip()
        scrape_profile_info(driver, target_username)

    finally:
        log_status("Closing the WebDriver... [Re-launching the Main menu]")
        driver.quit()

if __name__ == "__main__":
    main()
