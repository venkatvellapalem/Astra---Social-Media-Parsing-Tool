import os
import time
import instaloader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
import re

# Path for the geckodriver and settings
webdriver_path = '/home/deezsec/Downloads/geckodriver' 
credentials_file = 'active_instagram_credentials.txt'
firefox_options = Options()
firefox_options.set_preference("dom.webnotifications.enabled", False)
firefox_options.set_preference("media.volume_scale", "0.0")
firefox_options.set_preference("privacy.trackingprotection.enabled", True)

driver = webdriver.Firefox(service=Service(webdriver_path), options=firefox_options)

def log_status(message):
    ignore_patterns = [
        r"Warning: Image file .* not found\.",
    ]
    if any(re.search(pattern, message) for pattern in ignore_patterns):
        return
    #ANSI color codes   
    white_color = "\033[97m" 
    reset_color = "\033[0m"   
    print(f"{white_color}[ASTRA] {message}{reset_color}")

def save_screenshot(driver, file_name):
    driver.save_screenshot(file_name)
    log_status(f"Screenshot saved as {file_name}")

def create_pdf_report(screenshots, details, post_info, pdf_path):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []

    for image_file, detail in zip(screenshots, details):
        elements.append(Image(image_file, width=6*inch, height=4*inch))
        elements.append(Paragraph(detail, styles["BodyText"]))
        elements.append(Spacer(1, 12))

    if post_info:
        elements.append(Paragraph("Report succesfully finished!", styles["Heading2"]))
        elements.append(Spacer(1, 12))

        for post in post_info:
            if not os.path.isfile(post['image_path']):
                log_status(f"Warning: Image file {post['image_path']} not found.")
                continue
            
            elements.append(Paragraph(f"Caption: {post['caption']}", styles["BodyText"]))
            elements.append(Paragraph(f"Likes: {post['likes']}, Comments: {post['comments']}", styles["BodyText"]))
            elements.append(Image(post['image_path'], width=6*inch, height=4*inch))
            elements.append(Spacer(1, 12))

    doc.build(elements)
    log_status(f"PDF report created at {pdf_path}")

def get_credentials():
    if os.path.exists(credentials_file):
        log_status("Using saved credentials from previous session.")
        with open(credentials_file, 'r') as file:
            credentials = file.read().splitlines()
            if len(credentials) == 2:
                return credentials[0], credentials[1]
    else:
        username = input("Enter your Instagram username: ")
        password = input("Enter your Instagram password: ")
        with open(credentials_file, 'w') as file:
            file.write(f"{username}\n{password}")
        log_status("Credentials saved for future use.")
        return username, password

def login_instagram(driver, username, password):
    try:
        log_status("Navigating to Instagram login page...")
        driver.get("https://www.instagram.com/accounts/login/")
        
        log_status("Attempting to find username and password fields...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        log_status("Found username and password fields.")
        username_field.clear()
        password_field.clear()
        
        log_status("Entering credentials...")
        username_field.send_keys(username)
        password_field.send_keys(password)
        log_status("Credentials entered.")
        
        log_status("Submitting login form...")
        password_field.send_keys(Keys.RETURN)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.url_contains("instagram.com"))
        current_url = driver.current_url
        
        if "challenge" in current_url:
            log_status("Text verification challenge detected.")
            log_status("Please complete the challenge on the Instagram page.")
            input("Press Enter once the text verification challenge is completed...")

        log_status("Successfully logged in.")
        verification_prompt = input(white_color + "Did the page properly load without any Suspicious Login/2FA? (yes/no): ").strip().lower()
        if verification_prompt == "yes":
            log_status(white_color + "Waiting for input from user...")
            input(white_color + " Please press Enter once the entire page is loaded...")

        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='button']")))
            log_status("'Save Info' prompt detected.")
            save_info_button = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
            
            driver.execute_script("arguments[0].scrollIntoView(true);", save_info_button)
            time.sleep(1)  # Allow time
            driver.execute_script("arguments[0].click();", save_info_button)
            
            log_status("'Save Info' prompt closed.")
            time.sleep(5)  # Wait for loading
        except TimeoutException:
            log_status("No 'Save Info' prompt appeared.")
    except TimeoutException as e:
        log_status(f"Error during login process: {e}")
        raise e

def close_modal(driver):
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//button"))
        )
        close_button.click()
        log_status("Modal closed.")
    except TimeoutException:
        log_status("No modal to close.")
    except NoSuchElementException:
        log_status("Error: Could not find the close button for the modal.")

def detect_account_privacy(driver):
    try:
        private_indicator = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'This Account is Private')]"))
        )
        log_status("Account detected as private.")
        return "Private"
    except TimeoutException:
        log_status("Account detected as public.")
        return "Public"

def detect_account_verification(driver):
    try:
        verification_badge = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//span[@aria-label='Verified']"))
        )
        log_status("Account is verified.")
        return "Verified"
    except TimeoutException:
        log_status("Unable to check verification due to TimeOut.")
        return "Not Verified"

def click_element(driver, by, value, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((by, value)))
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)  # Allow time for scrolling to complete
            element.click()
            log_status(f"Clicked element with {by}={value} on attempt {attempt + 1}.")
            return
        except ElementClickInterceptedException:
            log_status(f"Element not clickable on attempt {attempt + 1}. Trying again...")
            time.sleep(2)
        except TimeoutException:
            log_status(f"Timed out trying to find the element with {by}={value}.")
            break

def scrape_account(driver, target_username):
    try:
        log_status(f"Navigating to {target_username}'s profile...")
        driver.get(f"https://www.instagram.com/{target_username}/")
        
        # Wait
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h2")))

        # Directory
        base_dir = os.path.join(os.getcwd(), f"{target_username}_instagram")
        latest_posts_dir = os.path.join(base_dir, "latest_posts")
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(latest_posts_dir, exist_ok=True)
        
        screenshots = []
        details = []
        post_info = []

        #main profile screenshot
        log_status("Capturing main profile screenshot...")
        time.sleep(2)
        main_profile_screenshot_path = os.path.join(base_dir, 'main_profile.png')
        save_screenshot(driver, main_profile_screenshot_path)
        details.append(f"Main Account screenshot of {target_username}")
        screenshots.append(main_profile_screenshot_path)
        
        log_status("Opening Followers list...")
        click_element(driver, By.PARTIAL_LINK_TEXT, "followers")
        time.sleep(4)  # Allow time for the list to load
        followers_screenshot_path = os.path.join(base_dir, 'followers.png')
        save_screenshot(driver, followers_screenshot_path)
        details.append(f"Followers list screenshot of {target_username}")
        screenshots.append(followers_screenshot_path)
        
        close_modal(driver)

        log_status("Opening Following list...")
        click_element(driver, By.PARTIAL_LINK_TEXT, "following")
        time.sleep(4)  # Allow time
        following_screenshot_path = os.path.join(base_dir, 'following.png')
        save_screenshot(driver, following_screenshot_path)
        details.append(f"Following list screenshot of {target_username}")
        screenshots.append(following_screenshot_path)
        
        close_modal(driver)

        log_status("Capturing latest posts screenshot...")
        recent_posts_screenshot_path = os.path.join(base_dir, 'recent_posts.png')
        save_screenshot(driver, recent_posts_screenshot_path)
        details.append(f"Recent posts screenshot of {target_username}")
        screenshots.append(recent_posts_screenshot_path)

        log_status("Downloading latest posts...")
        instaloader_instance = instaloader.Instaloader(dirname_pattern=latest_posts_dir)
        try:
            profile = instaloader.Profile.from_username(instaloader_instance.context, target_username)
            for post in profile.get_posts():
                if len(post_info) >= 3:
                    break
                instaloader_instance.download_post(post, target=latest_posts_dir)
                post_info.append({
                    'image_path': os.path.join(latest_posts_dir, f"{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"),  # Correct filename pattern
                    'caption': post.caption,
                    'likes': post.likes,
                    'comments': post.comments
                })
            log_status("Latest posts downloaded successfully.")
        except Exception as e:
            log_status(f"Error during scraping: {e}")

        #Generate PDF report
        pdf_path = os.path.join(base_dir, f"{target_username}_Report.pdf")
        create_pdf_report(screenshots, details, post_info, pdf_path)
        log_status(f"PDF report created at {pdf_path}")

    except Exception as e:
        log_status(f"Error during scraping: {e}")
    finally:
        driver.quit()
        log_status("WebDriver successfully closed.[Re-launching the Menu]")

# Main Execution
if __name__ == "__main__":
    username, password = get_credentials()
    login_instagram(driver, username, password)
    target_username = input(white_color + "Enter the target Instagram username to scrape: ")
    scrape_account(driver, target_username)
