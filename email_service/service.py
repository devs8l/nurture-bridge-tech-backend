"""
Email Service Module
Simple Gmail SMTP email sending
"""

import logging
from email.mime.text import MIMEText
from email.utils import formataddr
from smtplib import SMTP, SMTPException

# Basic Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for Gmail SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "meetayra@gmail.com"
SMTP_PASSWORD = "vgti gqyl sgck kpoz"
SYSTEM_FROM_EMAIL = "meetayra@gmail.com"


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an HTML email using Gmail's SMTP server.
    """
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SYSTEM_FROM_EMAIL]):
        logger.error("SMTP configuration is incomplete. Please check your settings.")
        return False

    try:
        # Send as HTML, not plain text
        msg = MIMEText(body, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr(("Nurture Bridge Tech", SYSTEM_FROM_EMAIL))
        msg["To"] = to_email

        with SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except SMTPException as smtp_err:
        logger.error(f"SMTP Error sending email to {to_email}: {smtp_err}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email to {to_email}: {e}")
        return False
