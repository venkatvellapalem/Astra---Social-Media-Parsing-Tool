import subprocess
import sys
import importlib.util
import os

WHITE = '\033[97m'
RESET = '\033[0m'

def colored_print(text):
    print(WHITE + text + RESET)

def log_status(message):
    """Log status with white color"""
    colored_print(f"[ASTRA] {message}")

def check_dependencies():
    banner = '''
    ░█▀▀▄░█▀▀░▀█▀░█▀▀▄░█▀▀▄  
    ▒█▄▄█░▀▀▄░░█░░█▄▄▀░█▄▄█   [Version 1.0.4] [Dev]
     █░▒█░▀▀▀░░▀░░▀░▀▀░▀░░▀   Developed by Team Twilight.
    
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
    ░░░░░░░░░▓█▓▓░░░░░░░░░░░░░░░░░
    ░░░░░▒▒▒░▓████▒░░░░░░░░░░░░░░░
    ░░░▒▒▓▓▓█▓▒▒▒▒▒▒▒▒▒▒▓█████▓▒░░ [Awaiting Target Information]
    ░░░▒▓▓▓▓█▓▒▒▒▒▒▒▒▒▒▒▓█████▓▒░░
    ░░░░░▒▒▒░▓████▒░░░░░░░░░░░░░░░
    ░░░░░░░░░▓█▓▓░░░░░░░░░░░░░░░░░
A Command-Line Python Framework to parse Social Media feeds and account information.\n'''

    print(WHITE + banner)
    print(WHITE + "[Starting the dependency check]")
    
    dependencies = ["selenium", "reportlab", "pyautogui", "instaloader"]
    missing_dependencies = []

    log_status("Checking Python version...")
    if sys.version_info[0] < 3:
        log_status("Python 3 is required. You are using Python 2.")
        sys.exit(1)
    log_status(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} is installed.")

    for dep in dependencies:
        if importlib.util.find_spec(dep) is None:
            log_status(f"{dep} is not installed.")
            missing_dependencies.append(dep)
        else:
            log_status(f"{dep} is installed.")

    if missing_dependencies:
        log_status("The following dependencies are missing:")
        for dep in missing_dependencies:
            log_status(f"  - {dep}")
        log_status("Please install the missing dependencies before continuing.")
        log_status("You can install them using pip:")
        log_status(f"pip install {' '.join(missing_dependencies)}")
        sys.exit(1)
    else:
        log_status("All dependencies are installed.")

def passive_menu():
    log_status("Launching Astra in Passive mode...")
    log_status("Please select one option to continue:")
    print(WHITE + """
    [1] Instagram
    [2] Facebook
    [3] Twitter
    [4] Google
    [5] WhatsApp
    [6] Telegram
    [0] Exit
    """)
    
    choice = input(WHITE + "Enter your choice: " + RESET)
    return choice

def active_menu():
    log_status("Launching Astra in Active mode...")
    log_status("Please select one option to continue:")
    print(WHITE + """
    [1] Instagram
    [2] Facebook
    [3] Twitter
    [4] Google
    [0] Exit
    """)
    
    choice = input(WHITE + "Enter your choice: " + RESET)
    return choice

def run_script(script_name):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        log_status(f"An error occurred while running {script_name}: {e}")

def check_credentials_file(platform, mode):
    if platform.lower() == "google":
        return True
    credentials_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{mode.lower()}_{platform.lower()}_credentials.txt")
    if os.path.exists(credentials_file):
        return True
    else:
        log_status(f"Error: Credentials file '{credentials_file}' not found.")
        return False

if __name__ == "__main__":
    check_dependencies()

    # Asking the user for credentials availability
    user_input = input(WHITE + "\nDo you have the suspect's credentials for the respective social media platforms? (Y/N): ").strip().upper()

    if user_input == 'Y':
        while True:
            choice = passive_menu()
            if choice == '1':
                if check_credentials_file("instagram", "passive"):
                    run_script("Astra_Passive_Instagram.py")
            elif choice == '2':
                if check_credentials_file("facebook", "passive"):
                    run_script("Astra_Passive_Facebook.py")
            elif choice == '3':
                if check_credentials_file("twitter", "passive"):
                    run_script("Astra_Passive_Twitter.py")
            elif choice == '4':
                if check_credentials_file("google", "passive"):
                    run_script("Astra_Passive_Google.py")
            elif choice == '5':
                if check_credentials_file("whatsapp", "passive"):
                    run_script("Astra_Passive_WhatsApp.py")
            elif choice == '6':
                if check_credentials_file("telegram", "passive"):
                    run_script("Astra_Passive_Telegram.py")
            elif choice == '0':
                log_status("Exiting the tool, Laterz Gatorz.")
                break
            else:
                log_status("Invalid choice. Please select a valid option.")
    elif user_input == 'N':
        while True:
            choice = active_menu()
            if choice == '1':
                if check_credentials_file("instagram", "active"):
                    run_script("Astra_Active_Instagram.py")
            elif choice == '2':
                if check_credentials_file("facebook", "active"):
                    run_script("Astra_Active_Facebook.py")
            elif choice == '3':
                if check_credentials_file("twitter", "active"):
                    run_script("Astra_Active_Twitter.py")
            elif choice == '4':
                if check_credentials_file("google", "active"):
                    run_script("Astra_Active_Google.py")
            elif choice == '0':
                log_status("Exiting the tool, Laterz Gatorz.")
                break
            else:
                log_status("Invalid choice. Please select a valid option.")
    else:
        log_status("Invalid input. Please run the script again and enter 'Y' or 'N'.")
