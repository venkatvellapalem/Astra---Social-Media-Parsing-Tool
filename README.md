# Astra
Astra is a powerful command-line Python framework designed for open-source intelligence (OSINT). It automates the process of gathering and parsing publicly available information from various social media platforms, consolidating user data and feeds into comprehensive, easy-to-read reports.
### Key Features
Astra operates in two distinct modes: **Active** and **Passive**.

Active Mode: Utilizes a user's own credentials to log in to social media platforms and scrape information from a target profile. This method is ideal for gathering more extensive and private data, such as a user's followers list, following list, saved posts, and direct message chat heads.

Passive Mode: Gathers publicly accessible information from social media platforms without the need for credentials. This is useful for initial reconnaissance and gathering public-facing data.
### Supported Platforms & Capabilities

| Platform | Mode | Information Scraped | Libraries Used |
| :--- | :--- | :--- | :--- |
| **Instagram** | Active | Profile information, followers/following lists, recent posts, saved posts, stories, tagged posts, highlights, and direct message chat heads.  | `selenium`, `instaloader`, `reportlab`  |
| | Passive | Profile information, followers/following lists, recent posts, likes, comments, and hashtags.  | `selenium`, `aiohttp`, `reportlab`  |
| **Twitter** | Active | Profile information (display name, bio, location, website, joined date), number of tweets, followers/following counts, and latest tweets.  | `selenium`, `reportlab`  |
| **Facebook** | Active | Profile homepage, about section, friends, photos, and videos.  | `selenium`, `reportlab`  |
| **Google** | Active | Google account information using the GHunt tool, including Gaia ID, profile picture, last profile edit, and associated services (e.g., Maps, Calendar).  | `subprocess`, `reportlab`  |

# Installation
### Prerequisites
Astra requires Python 3. You must also install the Geckodriver for Mozilla Firefox and specify its path in the respective Python scripts. The `webdriver_path` variable is currently set to `/home/venkatvellapalem/Downloads/geckodriver` but should be updated for your local environment.
### Dependencies
Install the necessary Python libraries using the `requirements.txt` file.
```bash
pip install -r requirements.txt
```
The dependencies include `selenium`, `reportlab`, `pyautogui`, `instaloader`, and `ghunt`.
### GHunt Setup
For the Google module, you must manually install and configure GHunt before running the script. The tool assumes **GHunt** is already set up and authenticated on your local machine.
# Usage
To start Astra, run the `main.py` script from your terminal:
```bash
python3 main.py
```
The tool will first check for all necessary dependencies. If any are missing, it will notify you and prompt you to install them.

Next, it will ask if you have the target's credentials. Your answer will determine whether Astra runs in **Active** or **Passive mode**.

Follow the on-screen prompts to select the social media platform and enter the target's username or email.

Astra will create a dedicated folder for the target and save all collected data, including a comprehensive PDF report with screenshots.
# License
Astra is licensed under the **MIT License**.

This license allows for the free use, modification, and distribution of the software, as long as the copyright notice and license text are included in all copies. The software is provided "as is," and the authors are not liable for any damages that may arise from its use.
