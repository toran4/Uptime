#!/usr/bin/env python
from __future__ import unicode_literals
from time import sleep, time, strftime
import requests
import io
import smtplib
import ssl
import sys
from smtp_config import user, sender, password, receivers, host, port
from email.message import EmailMessage
from email.utils import formatdate
import os


DELAY = int(os.environ.get("DELAY", "60"))  # Delay between site queries
EMAIL_INTERVAL = int(os.environ.get("EMAIL_INTERVAL", "1800"))  # Delay between alert emails
ALERT_COUNT_THRESHOLD = int(os.environ.get("ALERT_COUNT_THRESHOLD", "2")) # Number of required consecutive failures to alert
DATA_FOLDER = os.environ.get("DATA_FOLDER", "./")  # Folder for the sites file and monitor log

HEADERS = {'User-Agent': 'Uptime monitor'}

last_email_time = {}  # Monitored sites and timestamp of last alert sent
current_error_count = {}
monitor_log_path = os.path.join(DATA_FOLDER, "monitor.log")
sites_file_path = os.path.join(DATA_FOLDER, "sites.txt")

# Define escape sequences for colored terminal output
COLOR_DICT = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "bold": "\033[1m",
    "end": "\033[0m",
    }

# Message template for alert
ALERT_MESSAGE = "You are being notified that {site} is experiencing a {status} status!"
ALERT_SUBJECT = "ALERT: Monitor Service Notification for {site}"

# Message template for alert resolved
ALERT_RESOLVED_MESSAGE = "You are being notified that {site} is responding as expected again!"
ALERT_RESOLVED_SUBJECT = "RESOLVED: Monitor Service Notification for {site}"

def colorize(text, color):
    """Return input text wrapped in ANSI color codes for input color."""
    return COLOR_DICT[color] + str(text) + COLOR_DICT['end']


def error_log(site, status):
    """Log errors to stdout and log file, and send alert email via SMTP."""
    # Print colored status message to terminal
    print("\n({}) {} STATUS: {}".format(strftime("%a %b %d %Y %H:%M:%S"),
                                        site,
                                        colorize(status, "yellow"),
                                        ))
    # Log status message to log file
    with open(monitor_log_path, 'a') as log:
        log.write("({}) {} STATUS: {}\n".format(strftime("%a %b %d %Y %H:%M:%S"),
                                                site,
                                                status,
                                                )
                  )

def create_email_message(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receivers
    msg.add_header("Date", formatdate(localtime=True))
    msg.set_content(body)
    return msg

def send_alert(site, status):
    """If more than EMAIL_INTERVAL seconds since last email, resend email"""
    if (time() - last_email_time[site]) > EMAIL_INTERVAL and current_error_count[site] >= ALERT_COUNT_THRESHOLD:
        body = ALERT_MESSAGE.format(site=site, status=status)
        subject = ALERT_SUBJECT.format(site=site)
        mail_sent = send_email(subject, body)
        if mail_sent:
            last_email_time[site] = time()  # Update time of last email

def send_alert_resolved(site):
    body = ALERT_RESOLVED_MESSAGE.format(site=site)
    subject = ALERT_RESOLVED_SUBJECT.format(site=site)
    send_email(subject, body)

def send_email(subject, body):
    message = create_email_message(subject, body)
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host=host, port=port, context=context) as server:
            server.login(user, password)
            server.send_message(message)
            print(colorize("Successfully sent email", "green"))
            return True
    except Exception as e:
        print(colorize("Error sending email ({}:{})".format(host, port), "red"))
        print(e)
        return False


def ping(site):
    """Send GET request to input site and return status code"""
    try:
        resp = requests.get(site, headers=HEADERS)
    except Exception as e:
        print(colorize("Error pinging site {}".format(site), "red"))
        print(e)
        return -1 

    return resp.status_code


def get_sites():
    """Return list of unique URLs from input and sites.txt file."""
    sites = sys.argv[1:]  # Accept sites from command line input

    # Read in additional sites to monitor from sites.txt file
    try:
        sites += [site.strip() for site in io.open(sites_file_path, mode='r').readlines()]
    except IOError:
        print(colorize("No {} file found".format(sites_file_path), "red"))

    # Add protocol if missing in URL
    for site in range(len(sites)):
        if sites[site][:7] != "http://" and sites[site][:8] != "https://":
            sites[site] = "http://" + sites[site]

    # Eliminate exact duplicates in sites
    sites = list(set(sites))

    return sites


def main():
    sites = get_sites()

    for site in sites:
        print(colorize("Beginning monitoring of {}".format(site), "bold"))
        last_email_time[site] = 0  # Initialize timestamp as 0
        current_error_count[site] = 0

    while sites:
        try:
            for site in sites:
                status = ping(site)
                if status == 200:
                    if current_error_count[site] >= ALERT_COUNT_THRESHOLD:
                        print(colorize("Current active alert for {} resolved".format(site), "green"))
                        send_alert_resolved(site)
                    current_error_count[site] = 0
                    print(colorize(".", "green"), end="")
                    sys.stdout.flush()
                else:
                    current_error_count[site] += 1
                    error_log(site, status)
                    send_alert(site, status)
            sleep(DELAY)
        except KeyboardInterrupt:
            print(colorize("\n-- Monitoring canceled --", "red"))
            break
    else:
        print(colorize("No site(s) input to monitor!", "red"))


if __name__ == '__main__':
    main()
