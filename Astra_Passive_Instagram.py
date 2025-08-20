import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import random
import time
import asyncio
import aiohttp
import re
from functools import wraps

# Paths and Settings
webdriver_path = '/home/deezsec/Downloads/geckodriver'
credentials_file = 'passive_instagram_credentials.txt'
firefox_options = Options()
firefox_options.set_preference("dom.webnotifications.enabled", False)
firefox_options.set_preference("media.volume_scale", "0.0")
firefox_options.set_preference("privacy.trackingprotection.enabled", True)

# ANSI color codes for logging
white_color = "\033[97m"
reset_color = "\033[0m"

# Rate Limiting and Anti-Ban Measures
def random_delay(min_seconds=1, max_seconds=5):
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    
def human_like_scroll(driver):
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    for i in range(1, total_height, random.randint(100, 500)):
        driver.execute_script(f"window.scrollTo(0, {i});")
        random_delay(0.1, 0.3)

def rotate_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    return random.choice(user_agents)

# Error Handling and Retry Mechanism
def retry_on_exception(max_retries=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log_status(f"Error in {func.__name__}: {e}. Retrying in {delay} seconds...")
                    retries += 1
                    time.sleep(delay)
            log_status(f"Max retries reached for {func.__name__}. Giving up.")
            raise
        return wrapper
    return decorator

# Proxy Support
class ProxyManager:
    def __init__(self, proxy_list):
        self.proxies = proxy_list

    def get_random_proxy(self):
        return random.choice(self.proxies)

def setup_driver_with_proxy(proxy):
    firefox_options = Options()
    firefox_options.set_preference('network.proxy.type', 1)
    firefox_options.set_preference('network.proxy.socks', proxy['ip'])
    firefox_options.set_preference('network.proxy.socks_port', int(proxy['port']))
    firefox_options.set_preference('network.proxy.socks_version', 5)
    firefox_options.set_preference("general.useragent.override", rotate_user_agent())
    
    return webdriver.Firefox(service=Service(webdriver_path), options=firefox_options)

# Enhanced Data Extraction
@retry_on_exception(max_retries=3, delay=5)

def extract_post_data(driver, post_url):
    driver.get(post_url)
    random_delay(2, 5)

    post_data = {}
    try:
        # Extract likes
        likes_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//section[@class='_ae5m _ae5n _ae5o']//span"))
        )
        post_data['likes'] = likes_element.text

        # Extract comments
        comments = driver.find_elements(By.XPATH, "//ul[@class='_a9ym']//span[@class='_aacl _aaco _aacu _aacx _aad7 _aade']")
        post_data['comments'] = [comment.text for comment in comments[:5]]  # Get first 5 comments

        # Extract hashtags
        caption = driver.find_element(By.XPATH, "//div[@class='_a9zs']//span").text
        post_data['hashtags'] = re.findall(r"#(\w+)", caption)

    except Exception as e:
        log_status(f"Error extracting post data: {e}")

    return post_data

@retry_on_exception(max_retries=3, delay=5)    

def extract_user_posts(driver, username, num_posts=10):
    driver.get(f"https://www.instagram.com/{username}/")
    random_delay(2, 5)

    posts = []
    post_links = []

    while len(post_links) < num_posts:
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
        new_links = [link.get_attribute('href') for link in links if link.get_attribute('href') not in post_links]
        post_links.extend(new_links)
        human_like_scroll(driver)
        random_delay(1, 3)

    for link in post_links[:num_posts]:
        post_data = extract_post_data(driver, link)
        posts.append(post_data)

    return posts

# Asynchronous Processing
async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def process_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

async def async_extract_post_data(urls):
    results = await process_urls(urls)
    # Process the results (HTML content) here
    # You might need to use a HTML parser like BeautifulSoup to extract data
    return results


def log_status(message):
    print(f"{white_color}[ASTRA] {message}{reset_color}")

def save_screenshot(driver, file_name):
    driver.save_screenshot(file_name)
    log_status(f"Screenshot saved as {file_name}")

def create_pdf_report(screenshots, pdf_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle('CustomStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=12)
    
    elements = []
    
    for screenshot in screenshots:
        heading = os.path.basename(screenshot).split('.')[0]
        elements.append(Paragraph(heading, custom_style))
        elements.append(Spacer(1, 12))
        img = Image(screenshot, width=7*inch, height=5*inch)
        elements.append(img)
        elements.append(Spacer(1, 24))
    
    doc.build(elements)
    log_status(f"PDF report created at {pdf_path}")

def get_credentials():
    if os.path.exists(credentials_file):
        log_status("Using saved credentials.")
        with open(credentials_file, 'r') as file:
            credentials = file.read().splitlines()
            if len(credentials) == 2:
                return credentials[0], credentials[1]
    else:
        raise FileNotFoundError("Credentials file not found.")

@retry_on_exception(max_retries=3, delay=5)
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

        # Check for suspicious login attempt
        suspicious_login = input(f"{white_color}[ASTRA] Did the page properly load without any 'Suspicious Login/Two Step Authentication'? (Y/N): {reset_color}").strip().lower()
        if suspicious_login != 'y':
            input(f"{white_color}[ASTRA] Please complete the Suspicious login attempt / 2 Step Authentication checks and press Enter to continue the script...{reset_color}")

        WebDriverWait(driver, 10).until(EC.url_contains("instagram.com"))
        log_status("Successfully logged in.")
        random_delay(2, 5)
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='button']")))
            log_status("'Save Info' prompt detected.")
            save_info_button = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
            driver.execute_script("arguments[0].scrollIntoView(true);", save_info_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", save_info_button)
            log_status("'Save Info' prompt closed.")
            time.sleep(5)
        except TimeoutException:
            log_status("No 'Save Info' prompt appeared.")
    except TimeoutException as e:
        log_status(f"Error during login process: {e}")
        raise e

def close_modal(driver):
    log_status("Closing modal...")
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(2)  # Wait for modal to close

def open_chat_heads(driver, folder_path, username):
    try:
        log_status("Navigating to Direct Messages...")
        driver.get("https://www.instagram.com/direct/inbox/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@role='listitem']")))

        log_status("Scanning messages page...")
        screenshot_path = os.path.join(folder_path, f"{username}_messages_page.png")
        save_screenshot(driver, screenshot_path)

        log_status("Extracting chat heads...")
        chat_heads = driver.find_elements(By.XPATH, "//div[@role='listitem']")
        chat_screenshots = []

        for i, chat_head in enumerate(chat_heads[:5]):  # Limit to first 5 chats for testing
            try:
                log_status(f"Opening chat head {i + 1}...")
                chat_head.click()
                time.sleep(2)  # Wait for chat to open

                # Check if chat can be scrolled
                last_height = driver.execute_script("return document.body.scrollHeight")
                can_scroll = True
                scroll_attempt = 0
                max_scroll_attempts = 3

                while can_scroll and scroll_attempt < max_scroll_attempts:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        can_scroll = False
                    else:
                        last_height = new_height
                        scroll_attempt += 1

                # Take screenshot of entire chat
                chat_screenshot_path = os.path.join(folder_path, f"{username}_chat_{i + 1}.png")
                save_screenshot(driver, chat_screenshot_path)
                chat_screenshots.append(chat_screenshot_path)
                log_status(f"Screenshot taken for chat {i + 1}.")

                driver.back()
                time.sleep(2)  # Wait to return to inbox
            except Exception as e:
                log_status(f"Error interacting with chat head {i + 1}: {e}")

        return chat_screenshots
    except Exception as e:
        log_status(f"Error navigating to Direct Messages: {e}")
        return []

def capture_saved_posts(driver, username, folder_path):
    log_status(f"Navigating to Saved Posts for {username}...")
    driver.get(f"https://www.instagram.com/{username}/saved/all-posts/")
    time.sleep(5)  # Allow time for page to fully load

    screenshots = []
    scroll_attempt = 0
    max_scroll_attempts = 5
    last_height = driver.execute_script("return document.body.scrollHeight")

    # Take initial screenshot before scrolling
    screenshot_path = os.path.join(folder_path, f"{username}_saved_posts_initial.png")
    save_screenshot(driver, screenshot_path)
    screenshots.append(screenshot_path)

    while scroll_attempt < max_scroll_attempts:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Take screenshot after scrolling
        screenshot_path = os.path.join(folder_path, f"{username}_saved_posts_{scroll_attempt + 1}.png")
        save_screenshot(driver, screenshot_path)
        screenshots.append(screenshot_path)

        # Check if we can scroll further
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            log_status("Reached the end of saved posts or no more posts to load.")
            break
        last_height = new_height
        scroll_attempt += 1

    if scroll_attempt == 0:
        log_status("Saved posts are not extensive, stopping the scrolling.")
    else:
        log_status(f"Captured {len(screenshots)} screenshots of saved posts.")

    return screenshots
    
def extract_profile_info(driver, username):
    log_status(f"Extracting profile information for {username}...")
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(5)  # Allow time for page to fully load

    try:
        profile_info = {}
        profile_info['username'] = username
        
        # Extract bio
        try:
            bio = driver.find_element(By.XPATH, "//div[contains(@class, '_aa_c')]").text
            profile_info['bio'] = bio
        except NoSuchElementException:
            profile_info['bio'] = "No bio found"

        # Extract follower and following counts
        try:
            counts = driver.find_elements(By.XPATH, "//span[@class='_ac2a']")
            profile_info['posts_count'] = counts[0].text
            profile_info['followers_count'] = counts[1].text
            profile_info['following_count'] = counts[2].text
        except IndexError:
            log_status("Error extracting follower/following counts")

        # Extract profile picture URL
        try:
            profile_pic = driver.find_element(By.XPATH, "//img[@class='_aa8j']")
            profile_info['profile_picture_url'] = profile_pic.get_attribute('src')
        except NoSuchElementException:
            profile_info['profile_picture_url'] = "No profile picture found"

        return profile_info
    except Exception as e:
        log_status(f"Error extracting profile information: {e}")
        return None

def capture_stories(driver, username, folder_path):
    log_status(f"Attempting to capture stories for {username}...")
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(3)

    try:
        # Check if there's an active story
        story_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='_aarf _aarg']"))
        )
        story_button.click()
        time.sleep(2)

        stories_screenshots = []
        story_count = 0

        while True:
            # Capture the current story
            screenshot_path = os.path.join(folder_path, f"{username}_story_{story_count + 1}.png")
            save_screenshot(driver, screenshot_path)
            stories_screenshots.append(screenshot_path)
            story_count += 1

            # Try to move to the next story
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@class='_ac0d']"))
                )
                next_button.click()
                time.sleep(2)
            except TimeoutException:
                log_status(f"Captured {story_count} stories for {username}")
                break

        return stories_screenshots
    except TimeoutException:
        log_status(f"No active stories found for {username}")
        return []

def capture_screenshots(driver, username, folder_path):
    screenshots = []

    # Capture main profile
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(5)
    screenshot_path = os.path.join(folder_path, f"{username}_main_profile.png")
    save_screenshot(driver, screenshot_path)
    screenshots.append(screenshot_path)

    # Scroll down and capture second screenshot of profile
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(2)
    screenshot_path = os.path.join(folder_path, f"{username}_main_profile_scrolled.png")
    save_screenshot(driver, screenshot_path)
    screenshots.append(screenshot_path)

    # Capture followers modal
    try:
        log_status("Opening Followers list...")
        followers_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers/')]"))
        )
        followers_link.click()
        time.sleep(5)
        screenshot_path = os.path.join(folder_path, f"{username}_followers.png")
        save_screenshot(driver, screenshot_path)
        screenshots.append(screenshot_path)
        close_modal(driver)
    except Exception as e:
        log_status(f"Error capturing followers screenshot: {e}")

    # Capture following modal
    try:
        log_status("Opening Following list...")
        following_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following/')]"))
        )
        following_link.click()
        time.sleep(5)
        screenshot_path = os.path.join(folder_path, f"{username}_following.png")
        save_screenshot(driver, screenshot_path)
        screenshots.append(screenshot_path)
        close_modal(driver)
    except Exception as e:
        log_status(f"Error capturing following screenshot: {e}")

    # Capture saved posts
    saved_posts_screenshots = capture_saved_posts(driver, username, folder_path)
    screenshots.extend(saved_posts_screenshots)

    # Capture stories
    stories_screenshots = capture_stories(driver, username, folder_path)
    screenshots.extend(stories_screenshots)

    # Capture tagged posts
    driver.get(f"https://www.instagram.com/{username}/tagged/")
    time.sleep(5)
    screenshot_path = os.path.join(folder_path, f"{username}_tagged.png")
    save_screenshot(driver, screenshot_path)
    screenshots.append(screenshot_path)

    # Capture highlights
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(5)
    screenshot_path = os.path.join(folder_path, f"{username}_highlights.png")
    save_screenshot(driver, screenshot_path)
    screenshots.append(screenshot_path)

    # Capture chat heads
    chat_screenshots = open_chat_heads(driver, folder_path, username)
    screenshots.extend(chat_screenshots)

    return screenshots

if __name__ == "__main__":
    driver = None
    try:
        username, password = get_credentials()

        folder_path = os.path.join(os.getcwd(), f"{username}_instagram")
        os.makedirs(folder_path, exist_ok=True)
        log_status(f"Created folder: {folder_path}")

        # Initialize the WebDriver only once
        log_status("Initializing WebDriver...")
        driver = webdriver.Firefox(service=Service(webdriver_path), options=firefox_options)

        login_instagram(driver, username, password)

        profile_info = extract_profile_info(driver, username)
        if profile_info:
            with open(os.path.join(folder_path, f"{username}_profile_info.json"), 'w') as f:
                json.dump(profile_info, f, indent=4)
            log_status(f"Profile information saved for {username}")

        screenshots = capture_screenshots(driver, username, folder_path)

        pdf_path = os.path.join(folder_path, f"{username}_instagram_report.pdf")
        create_pdf_report(screenshots, pdf_path)

        log_status("Closing and cleaning...")

    except Exception as e:
        log_status(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()
            log_status("WebDriver successfully closed.[Re-launching Menu]")
