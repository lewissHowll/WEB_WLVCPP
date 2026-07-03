"""Sends contact-form emails via SMTP.

Configured entirely through environment variables, so credentials never
live in the repo:

    SMTP_HOST       required — e.g. smtp.fasthosts.co.uk, smtp.gmail.com
    SMTP_PORT       optional, default 587 (STARTTLS)
    SMTP_USERNAME   required — the mailbox to send FROM
    SMTP_PASSWORD   required
    SMTP_FROM       optional, defaults to SMTP_USERNAME
    CONTACT_TO_EMAIL   optional, defaults to lewis.howl@developyn.com

If SMTP_HOST/USERNAME/PASSWORD aren't set, send_contact_email() raises
RuntimeError — main.py turns that into a clear 503 rather than a silent
failure, so a misconfigured deployment fails loudly instead of quietly
eating messages.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM = os.environ.get("SMTP_FROM") or SMTP_USERNAME
CONTACT_TO_EMAIL = os.environ.get("CONTACT_TO_EMAIL", "lewis.howl@developyn.com")

SMTP_CONFIGURED = bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)


def send_contact_email(name: str, from_email: str, subject: str, comment: str) -> None:
    if not SMTP_CONFIGURED:
        raise RuntimeError(
            "Contact form isn't configured yet — set SMTP_HOST, SMTP_USERNAME "
            "and SMTP_PASSWORD env vars. See README's 'Contact form' section."
        )

    body = f"From: {name} <{from_email}>\n\n{comment}"
    msg = MIMEText(body)
    msg["Subject"] = f"[WLVCPP contact] {subject}"
    msg["From"] = formataddr((name, SMTP_FROM))
    msg["To"] = CONTACT_TO_EMAIL
    msg["Reply-To"] = from_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [CONTACT_TO_EMAIL], msg.as_string())
