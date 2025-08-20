import subprocess
import sys
import json
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from shutil import which
import socket

WHITE = '\033[97m'
RESET = '\033[0m'

def colored_print(text, color=WHITE):
    print(color + text + RESET)

def log_status(message):
    colored_print(f"[ASTRA] {message}")

def check_network():
    try:
        # Test DNS resolution by trying to reach a common server (e.g., Google DNS)
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

def find_ghunt_binary():
    ghunt_path = which("ghunt")
    if not ghunt_path:
        raise FileNotFoundError("Ghunt binary not found. Ensure Ghunt is installed and available in PATH.")
    return ghunt_path

def run_ghunt_command(email):
    log_status("Running Ghunt command...")
    try:
        ghunt_path = find_ghunt_binary()
        cmd = f"{ghunt_path} email {email}"
        log_status(f"Executing command: {cmd}")
        
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        log_status("Ghunt command completed successfully.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        log_status(f"An error occurred while running Ghunt: {e}")
        colored_print(f"STDOUT: {e.stdout}")
        colored_print(f"STDERR: {e.stderr}")
        return None

def parse_ghunt_data(output):
    log_status("Parsing Ghunt data...")
    data = {}

    # Manually map the expected output format to key-value pairs
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()
    
    # Handle additional parsing for specific sections like profile picture, maps, etc.
    # Checking for common keywords and formatting data appropriately
    if 'Custom profile picture' in output:
        data['Profile Picture'] = output.split('=> ')[1].split()[0]  # Extracts profile picture URL

    return data

def create_pdf_report(data, email, output_file):
    log_status("Creating PDF report...")
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Ghunt Report for {email}", styles['Title']))

    if not data:
        elements.append(Paragraph("No data retrieved.", styles['BodyText']))
    else:
        # Creating the table with the required details
        table_data = [
            [Paragraph('GHunt Version', styles['BodyText']), Paragraph('2.2.0 (Wardriving Edition)', styles['BodyText'])],
            [Paragraph('Status', styles['BodyText']), Paragraph('You are up to date!', styles['BodyText'])],
            [Paragraph('Session', styles['BodyText']), Paragraph('Stored session loaded, Authenticated', styles['BodyText'])],
            [Paragraph('Email', styles['BodyText']), Paragraph(data.get('Email', 'Not available'), styles['BodyText'])],
            [Paragraph('Gaia ID', styles['BodyText']), Paragraph(data.get('Gaia ID', 'Not available'), styles['BodyText'])],
            [Paragraph('Profile Picture', styles['BodyText']), Paragraph(data.get('Profile Picture', 'No profile picture'), styles['BodyText'])],
            [Paragraph('Profile Edit', styles['BodyText']), Paragraph(data.get('Last profile edit', 'Not available'), styles['BodyText'])],
            [Paragraph('User Type', styles['BodyText']), Paragraph(data.get('User types', 'Unknown'), styles['BodyText'])],
            [Paragraph('Entity Type', styles['BodyText']), Paragraph(data.get('Entity Type', 'Unknown'), styles['BodyText'])],
            [Paragraph('Customer ID', styles['BodyText']), Paragraph(data.get('Customer ID', 'Not found'), styles['BodyText'])],
            [Paragraph('Google Plus User', styles['BodyText']), Paragraph(data.get('Entreprise User', 'False'), styles['BodyText'])],
            [Paragraph('Play Games Profile', styles['BodyText']), Paragraph('No player profile found.', styles['BodyText'])],
            [Paragraph('Maps Profile Page', styles['BodyText']), Paragraph(data.get('Profile page', 'No profile page'), styles['BodyText'])],
            [Paragraph('Maps Reviews', styles['BodyText']), Paragraph('Please check manually..', styles['BodyText'])],
            [Paragraph('Google Calendar', styles['BodyText']), Paragraph('No public Google Calendar.', styles['BodyText'])]
        ]

        # Table formatting
        table = Table(table_data, colWidths=[200, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
    
    doc.build(elements)
    log_status(f"PDF report created successfully: {output_file}")

def main():
    colored_print("Welcome to Astra Ghunt Module")
    
    log_status('''Please configure and login to GHunt manually before running this script: https://github.com/mxrch/GHunt
This tool assumes that you have already installed and configured ghunt locally.
      ''')
      
    email = input(WHITE + "Enter the target Google account email: " + RESET)

    log_status("Starting Ghunt information gathering...")

    # Check network before running Ghunt
    if check_network():
        json_output = run_ghunt_command(email)

        if json_output:
            data = parse_ghunt_data(json_output)
            output_file = f"google_{email.replace('@', '_at_')}.pdf"
            create_pdf_report(data, email, output_file)
            colored_print(f"Ghunt report generated: {output_file}")
        else:
            log_status("Failed to retrieve data from Ghunt.")
            create_pdf_report(None, email, f"google_{email.replace('@', '_at_')}.pdf")
    else:
        log_status("No internet connection detected. Please check your network.")

    log_status("Ghunt module execution completed.")

if __name__ == "__main__":
    main()
