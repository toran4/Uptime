#!/usr/bin/env python
import os

# Login email and password for account sending alerts
_sender = "monitor@example.com"
_user = "exampleuser"
_password = "examplepassword"

sender = os.environ.get("EMAIL_SENDER", _sender)
user = os.environ.get("SMTP_USER", _user)
password = os.environ.get("SMTP_PASSWORD", _password)

# Host and port for smtp server sending alerts
_host = "mail.example.com"
_port = "465"

host = os.environ.get("SMTP_HOST", _host)
port = int(os.environ.get("SMTP_PORT", _port))

# Recipients that will get alert
_receivers = "john.doe@gmail.com"

receivers = list1 = [i.strip() for i in os.environ.get("EMAIL_RECEIVERS", _receivers).split(",")]

