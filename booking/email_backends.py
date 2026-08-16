"""
Minimal Django email backend that sends via SendGrid's HTTPS API (v3)
instead of SMTP. Many PaaS hosts (Railway included) block or silently drop
outbound SMTP connections as an anti-spam measure - plain HTTPS isn't
affected, so this is the reliable way to send from a hosted app.
"""

from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

API_URL = "https://api.sendgrid.com/v3/mail/send"


def _address(raw):
    name, email = parseaddr(raw)
    return {"email": email, "name": name} if name else {"email": email}


class SendGridAPIBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent = 0
        for message in email_messages:
            payload = {
                "personalizations": [
                    {"to": [_address(addr) for addr in message.to]}
                ],
                "from": _address(message.from_email),
                "subject": message.subject,
                "content": [{"type": "text/plain", "value": message.body}],
            }
            try:
                response = requests.post(
                    API_URL,
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
                    timeout=10,
                )
                response.raise_for_status()
            except requests.RequestException:
                if not self.fail_silently:
                    raise
                continue
            sent += 1
        return sent
