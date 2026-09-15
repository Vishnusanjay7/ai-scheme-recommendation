"""
Email Notification Service
--------------------------
Provides a provider-agnostic email delivery interface for citizen deadline alerts.
Configuration is read strictly from environment variables:
  - SMTP_HOST
  - SMTP_PORT (default: 587)
  - SMTP_USER
  - SMTP_PASSWORD
  - NOTIFICATION_FROM_EMAIL (default: noreply@schemesetu.gov.in)

GUARANTEES:
1. Missing or invalid email configuration will NOT break in-app notification generation.
2. Provider credentials are never exposed or hardcoded.
3. Successful delivery sets status to SENT; failure/unconfigured leaves status PENDING or FAILED.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger("email_service")


class EmailService:
    """Service for dispatching transactional deadline alert emails to citizens."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        self.host = host or os.getenv("SMTP_HOST")
        port_val = port or os.getenv("SMTP_PORT", "587")
        try:
            self.port = int(port_val)
        except (ValueError, TypeError):
            self.port = 587
        self.user = user or os.getenv("SMTP_USER")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("NOTIFICATION_FROM_EMAIL", "noreply@schemesetu.gov.in")

    def is_configured(self) -> bool:
        """Check whether SMTP settings are configured."""
        return bool(self.host and self.user and self.password)

    def send_deadline_notification(
        self,
        to_email: str,
        citizen_name: str,
        scheme_name: str,
        notification_type: str,
        days_remaining: int,
        official_url: Optional[str] = None,
    ) -> bool:
        """
        Send a deadline alert email to the citizen.
        Returns:
          True if successfully delivered via SMTP.
          False if unconfigured, or delivery failed.
        """
        if not to_email or not to_email.strip():
            logger.warning("Email send skipped: recipient address is empty.")
            return False

        if not self.is_configured():
            logger.info(
                f"SMTP unconfigured. Skipping email dispatch to {to_email} for scheme '{scheme_name}'."
            )
            return False

        # Construct email content
        urgency_label = "URGENT DEADLINE" if notification_type == "DEADLINE_URGENT" else (
            "CLOSING TODAY" if notification_type == "DEADLINE_TODAY" else "DEADLINE APPROACHING"
        )
        subject = f"[{urgency_label}] Application Deadline Alert: {scheme_name}"

        body_text = (
            f"Dear {citizen_name or 'Citizen'},\n\n"
            f"This is an official alert regarding your saved welfare scheme:\n\n"
            f"Scheme: {scheme_name}\n"
            f"Status: {urgency_label}\n"
            f"Days Remaining: {days_remaining} day(s)\n\n"
            f"Please ensure you complete your application on the official government portal before the window closes.\n"
        )
        if official_url:
            body_text += f"Official Portal: {official_url}\n\n"
        body_text += "Regards,\nSchemeSetu AI Government Portal"

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body_text, "plain"))

            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)

            logger.info(f"Deadline alert email successfully delivered to {to_email} for '{scheme_name}'.")
            return True
        except Exception as exc:
            logger.error(f"Failed to deliver deadline alert email to {to_email}: {str(exc)}")
            return False
