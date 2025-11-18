"""
Mailjet Email Backend for Django.

Uses Mailjet's HTTP API instead of SMTP to send emails.
This bypasses potential SMTP port blocking on hosting platforms like Render.
"""

import logging

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from mailjet_rest import Client

logger = logging.getLogger(__name__)


class MailjetBackend(BaseEmailBackend):
    """
    Email backend using Mailjet HTTP API v3.1.

    Configuration required in settings:
        MAILJET_API_KEY: Your Mailjet API key
        MAILJET_SECRET_KEY: Your Mailjet Secret key
        DEFAULT_FROM_EMAIL: Default sender email address

    Environment variables:
        MAILJET_API_KEY=<your_api_key>
        MAILJET_SECRET_KEY=<your_secret_key>
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, "MAILJET_API_KEY", None)
        self.secret_key = getattr(settings, "MAILJET_SECRET_KEY", None)

        if not self.api_key or not self.secret_key:
            logger.error(
                "Mailjet API credentials not configured. Set MAILJET_API_KEY and "
                "MAILJET_SECRET_KEY."
            )
            if not fail_silently:
                raise ValueError("Mailjet API credentials missing in settings")

        self.client = Client(auth=(self.api_key, self.secret_key), version="v3.1")

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number sent.

        Args:
            email_messages: List of Django EmailMessage objects

        Returns:
            int: Number of emails successfully sent
        """
        if not email_messages:
            return 0

        num_sent = 0

        for message in email_messages:
            try:
                sent = self._send(message)
                if sent:
                    num_sent += 1
            except Exception as exc:
                logger.error(f"Failed to send email via Mailjet: {exc}", exc_info=True)
                if not self.fail_silently:
                    raise

        return num_sent

    def _send(self, message):
        """
        Send a single EmailMessage via Mailjet API.

        Args:
            message: Django EmailMessage object

        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Extract HTML content if available
        html_content = None
        if message.content_subtype == "html":
            html_content = message.body
            text_content = ""  # HTML is primary
        elif hasattr(message, "alternatives") and message.alternatives:
            # Check for HTML in alternatives (typical for EmailMultiAlternatives)
            for content, mimetype in message.alternatives:
                if mimetype == "text/html":
                    html_content = content
                    break
            text_content = message.body
        else:
            text_content = message.body

        # Build recipients list
        to_recipients = [{"Email": email, "Name": email.split("@")[0]} for email in message.to]

        # Build Mailjet API payload
        data = {
            "Messages": [
                {
                    "From": {
                        "Email": message.from_email or settings.DEFAULT_FROM_EMAIL,
                        "Name": getattr(settings, "DEFAULT_FROM_NAME", "GeoAnnotator"),
                    },
                    "To": to_recipients,
                    "Subject": message.subject,
                }
            ]
        }

        # Add text/html content
        if html_content:
            data["Messages"][0]["HTMLPart"] = html_content
        if text_content:
            data["Messages"][0]["TextPart"] = text_content

        # Add CC if present
        if message.cc:
            data["Messages"][0]["Cc"] = [{"Email": email} for email in message.cc]

        # Add BCC if present
        if message.bcc:
            data["Messages"][0]["Bcc"] = [{"Email": email} for email in message.bcc]

        # Log attempt
        logger.info(
            f"Sending email via Mailjet API: '{message.subject}' to {[r['Email'] for r in to_recipients]}"
        )

        # Send via Mailjet API
        try:
            result = self.client.send.create(data=data)

            if result.status_code == 200:
                logger.info(f"✓ Email sent successfully via Mailjet API: {message.subject}")
                return True
            else:
                logger.error(
                    f"✗ Mailjet API error: Status {result.status_code}, Response: {result.json()}"
                )
                if not self.fail_silently:
                    raise RuntimeError(f"Mailjet API returned status {result.status_code}")
                return False

        except Exception as exc:
            logger.error(f"✗ Mailjet API request failed: {exc}", exc_info=True)
            if not self.fail_silently:
                raise
            return False
