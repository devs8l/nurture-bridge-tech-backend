"""
Email Service Module
Simple Gmail SMTP email sending
"""

import logging
from email.mime.text import MIMEText
from email.utils import formataddr
from smtplib import SMTP_SSL, SMTPException

from config.settings import settings

# Basic Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
SMTP_SERVER = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USERNAME = settings.SMTP_USERNAME
SMTP_PASSWORD = settings.SMTP_PASSWORD
SYSTEM_FROM_EMAIL = settings.SMTP_FROM_EMAIL


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an HTML email using Gmail's SMTP server over SSL (port 465).
    This uses SMTP_SSL instead of STARTTLS to work with cloud platforms like Render.
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

        # Use SMTP_SSL for port 465 (no starttls needed)
        with SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
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
