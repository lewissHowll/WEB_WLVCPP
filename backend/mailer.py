"""Sends contact-form emails via the Resend HTTP API.

Not SMTP: free-tier hosts (Render included) block outbound SMTP ports to
prevent spam abuse, so a raw smtplib connection fails with a network error
regardless of correct credentials. Resend's API runs over plain HTTPS, which
isn't blocked.

    RESEND_API_KEY    required — from resend.com/api-keys
    EMAIL_FROM         optional, default "WLVCPP <onboarding@resend.dev>"
    CONTACT_TO_EMAIL   optional, defaults to lewis.howl@developyn.com

Resend's shared onboarding@resend.dev sender can only deliver to the email
address your Resend account was signed up with — fine here, since every
contact-form message goes to the same fixed CONTACT_TO_EMAIL address. Sign
up for Resend using that same address and no domain verification is needed
at all. To send from your own domain instead (e.g. contact@bioportide.co.uk)
or to different recipients, verify a domain in Resend and set EMAIL_FROM
to an address on it.

If RESEND_API_KEY isn't set, send_contact_email() raises RuntimeError —
main.py turns that into a clear 503 rather than a silent failure, so a
misconfigured deployment fails loudly instead of quietly eating messages.
"""
import os
import requests

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "WLVCPP <onboarding@resend.dev>")
CONTACT_TO_EMAIL = os.environ.get("CONTACT_TO_EMAIL", "lewis.howl@developyn.com")

RESEND_CONFIGURED = bool(RESEND_API_KEY)

RESEND_API_URL = "https://api.resend.com/emails"


def send_contact_email(name: str, from_email: str, subject: str, comment: str) -> None:
    if not RESEND_CONFIGURED:
        raise RuntimeError(
            "Contact form isn't configured yet — set the RESEND_API_KEY env var. "
            "See README's 'Contact form' section."
        )

    body = f"From: {name} <{from_email}>\n\n{comment}"

    try:
        resp = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": EMAIL_FROM,
                "to": [CONTACT_TO_EMAIL],
                "subject": f"[WLVCPP contact] {subject}",
                "text": body,
                "reply_to": from_email,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Couldn't reach Resend's API: {exc}") from exc

    if resp.status_code >= 400:
        raise RuntimeError(f"Resend API error ({resp.status_code}): {resp.text}")
