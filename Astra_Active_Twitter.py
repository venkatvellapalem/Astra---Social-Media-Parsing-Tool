import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

#Path
webdriver_path = '/home/deezsec/Downloads/geckodriver'  # Update the path according to your system
credentials_file = 'active_twitter_credentials.txt'
firefox_options = Options()
firefox_options.set_preference("dom.webnotifications.enabled", False)
firefox_options.set_preference("media.volume_scale", "0.0")
firefox_options.set_preference("privacy.trackingprotection.enabled", True)

#Selenium WebDriver
driver = webdriver.Firefox(service=Service(webdriver_path), options=firefox_options)

def log_status(message):
    print(f"\033[97m[ASTRA] {message}\033[0m")

WHITE = "\033[97m"
RESET = "\033[0m"


def save_screenshot(driver, file_name):
    driver.save_screenshot(file_name)
    log_status(f"Screenshot saved as {file_name}")

def create_pdf_report(screenshots, details, tweet_info, profile_info, pdf_path):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []

    elements.append(Paragraph("Twitter Profile Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    if screenshots:
        elements.append(Image(screenshots[0], width=6*inch, height=4*inch))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Profile Information:", styles["Heading2"]))
    for key, value in profile_info.items():
        elements.append(Paragraph(f"{key}: {value}", styles["BodyText"]))
    elements.append(Spacer(1, 12))

    for image_file, detail in zip(screenshots[1:], details):
        elements.append(Image(image_file, width=6*inch, height=4*inch))
        elements.append(Paragraph(detail, styles["BodyText"]))
        elements.append(Spacer(1, 12))

    #Latest Tweets
    if tweet_info:
        elements.append(Paragraph("Latest Tweets:", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        for tweet in tweet_info:
            elements.append(Paragraph(f"Tweet: {tweet['text']}", styles["BodyText"]))
            elements.append(Paragraph(f"Date: {tweet['date']}", styles["BodyText"]))
            if 'image' in tweet:
                elements.append(Image(tweet['image'], width=6*inch, height=4*inch))
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
        username = input("Enter your Twitter username: ")
        password = input("Enter your Twitter password: ")
        with open(credentials_file, 'w') as file:
            file.write(f"{username}\n{password}")
        log_status("Credentials saved for future use.")
        return username, password

def login_twitter(driver, username, password):
    try:
        log_status("Navigating to Twitter login page...")
        driver.get("https://twitter.com/login")
        log_status("Attempting to find username field...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "text")))
        username_field = driver.find_element(By.NAME, "text")
        username_field.send_keys(username)
        username_field.send_keys(Keys.RETURN)
        
        # Check for suspicious login attempt after entering username
        input("\033[97m[ASTRA] Do you see any suspicious login page/2FA? If yes, complete it and press Enter to continue...\033[0m")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        log_status("Credentials entered.")
        
        log_status("Submitting login form...")
        password_field.send_keys(Keys.RETURN)
        
        log_status("Waiting for login to complete...")
        WebDriverWait(driver, 10).until(EC.url_contains("home"))
        log_status("Successfully logged in.")
    except TimeoutException as e:
        log_status(f"Error during login process: {e}")
        raise e

def close_modal(driver):
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@aria-label='Close']"))
        )
        close_button.click()
        log_status("Modal closed.")
    except TimeoutException:
        log_status("No modal to close.")
    except NoSuchElementException:
        log_status("Error: Could not find the close button for the modal.")

def download_latest_tweets(driver, tweet_count=10):
    tweets = []
    try:
        log_status("Scrolling to load tweets...")
        for _ in range(tweet_count // 3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)

        tweet_elements = driver.find_elements(By.XPATH, "//article[@role='article']")
        
        for i in range(len(tweet_elements)):
            try:
                tweet_text = tweet_elements[i].text
                tweet_date = tweet_elements[i].find_element(By.XPATH, ".//time").get_attribute("datetime")

                #take screenshot of each tweet
                tweet_screenshot = os.path.join(folder_path, f"tweet_{i + 1}.png")
                tweet_elements[i].screenshot(tweet_screenshot)

                tweets.append({'text': tweet_text, 'date': tweet_date, 'image': tweet_screenshot})

            except StaleElementReferenceException:
                log_status(f"Error while downloading tweet {i + 1}: Tweet element became stale.")
                continue

    except Exception as e:
        log_status(f"Error while downloading tweets: {str(e)}")

    return tweets

def scrape_profile_information(driver, target_username):
    profile_info = {}
    try:
        profile_info['Username'] = target_username
        profile_info['Display Name'] = driver.find_element(By.XPATH, "//div[@data-testid='UserName']//span").text
        profile_info['Bio'] = driver.find_element(By.XPATH, "//div[@data-testid='UserDescription']").text
        profile_info['Profile Picture URL'] = driver.find_element(By.XPATH, "//div[@data-testid='UserAvatar']//img").get_attribute('src')
        profile_info['Banner Image URL'] = driver.find_element(By.XPATH, "//div[@data-testid='UserBanner']//img").get_attribute('src')
        profile_info['Location'] = driver.find_element(By.XPATH, "//span[text()='Location']//following-sibling::span").text
        profile_info['Website'] = driver.find_element(By.XPATH, "//span[text()='Website']//following-sibling::span/a").text
        profile_info['Joined Date'] = driver.find_element(By.XPATH, "//span[text()='Joined']//following-sibling::span").text
        profile_info['Number of Tweets'] = driver.find_element(By.XPATH, "//a[contains(@href, '/with_replies')]//span").text
        profile_info['Number of Followers'] = driver.find_element(By.XPATH, "//a[@href='/" + target_username + "/followers']//span").text
        profile_info['Number of Following'] = driver.find_element(By.XPATH, "//a[@href='/" + target_username + "/following']//span").text

        log_status("Profile information scraped.")
    except NoSuchElementException as e:
        log_status(f"Error while scraping profile information: {str(e)}")

    return profile_info

def take_profile_home_screenshot(driver, target_username):
    screenshot_path = os.path.join(folder_path, f"{target_username}_profile_home.png")
    save_screenshot(driver, screenshot_path)
    return screenshot_path

def scrape_followers_and_following(driver, target_username, list_type="followers"):
    screenshot_path = os.path.join(folder_path, f"{target_username}_{list_type}_list.png")
    try:
        log_status(f"Navigating to {list_type} page...")
        list_url = f"https://twitter.com/{target_username}/{list_type}"
        driver.get(list_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers') or contains(@href, '/following')]"))
        )

        log_status(f"Scrolling to load {list_type}...")
        time.sleep(2)
        save_screenshot(driver, screenshot_path)

        log_status(f"{list_type.capitalize()} screenshot captured.")
    except Exception as e:
        log_status(f"Error while capturing {list_type} screenshot: {str(e)}")

    return screenshot_path

def run_tool(target_username):
    try:
        username, password = get_credentials()

        #logging
        login_twitter(driver, username, password)

        #folder creation
        global folder_path
        folder_path = f"{target_username}_twitter"
        os.makedirs(folder_path, exist_ok=True)

        #target profile
        log_status(f"Navigating to {target_username}'s profile...")
        driver.get(f"https://twitter.com/{target_username}")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        close_modal(driver)

        profile_info = scrape_profile_information(driver, target_username)

        profile_home_screenshot = take_profile_home_screenshot(driver, target_username)

        tweet_info = download_latest_tweets(driver, tweet_count=10)

        screenshots = {
            'profile': profile_home_screenshot,
            'followers': scrape_followers_and_following(driver, target_username, 'followers'),
            'following': scrape_followers_and_following(driver, target_username, 'following')
        }

        #PDF report
        pdf_path = os.path.join(folder_path, f"{target_username}_report.pdf")
        create_pdf_report(
            list(screenshots.values()),  # All screenshots
            ["Profile Home Screenshot", "Followers Screenshot", "Following Screenshot"], 
            tweet_info,
            profile_info,
            pdf_path
        )

    except WebDriverException as e:
        log_status(f"Webdriver error occurred: {e}")
    finally:
        log_status("Cleaning and closing browser...")
        driver.quit()

# Execute
if __name__ == "__main__":
    target_username = input(WHITE + "Enter the target Twitter username (without @): ")
    run_tool(target_username)
