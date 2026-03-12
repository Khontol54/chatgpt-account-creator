"""
Email manager – handles temporary email generation and inbox polling
for the verification step of account creation.
"""

import imaplib
import re
import smtplib
import time
from email.mime.text import MIMEText
from typing import Optional

from config import config
from utils.logger import get_logger

logger = get_logger("email_manager")


class EmailManager:
    """
    Manages email addresses used during account creation.

    Supports three providers:
      - ``tempmail``  – generates a random address via the public Guerrilla Mail API
      - ``gmail``     – uses a configured Gmail account (IMAP + app-specific password)
      - ``custom``    – uses any SMTP/IMAP server configured via environment variables
    """

    # ------------------------------------------------------------------ #
    # Address generation                                                   #
    # ------------------------------------------------------------------ #

    def generate_email(self) -> str:
        """Return a fresh email address based on the configured provider."""
        if config.EMAIL_PROVIDER == "tempmail":
            return self._generate_tempmail()
        if config.EMAIL_PROVIDER == "gmail":
            return config.GMAIL_USERNAME
        if config.EMAIL_PROVIDER == "custom":
            return config.SMTP_USER
        raise ValueError(f"Unknown EMAIL_PROVIDER: {config.EMAIL_PROVIDER!r}")

    def _generate_tempmail(self) -> str:
        """
        Create a random address on the Guerrilla Mail service.

        Falls back to a UUID-based placeholder if the HTTP request fails
        so that the rest of the creation flow is not interrupted.
        """
        import uuid

        try:
            import requests

            session = requests.Session()
            resp = session.get(
                "https://api.guerrillamail.com/ajax.php",
                params={"f": "get_email_address"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            email = data.get("email_addr", "")
            if email:
                logger.debug("Guerrilla Mail address: %s", email)
                return email
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not reach Guerrilla Mail API: %s", exc)

        # Fallback – placeholder address (won't receive real mail)
        return f"chatgpt.{uuid.uuid4().hex[:8]}@guerrillamailblock.com"

    # ------------------------------------------------------------------ #
    # Inbox polling                                                        #
    # ------------------------------------------------------------------ #

    def wait_for_verification_email(
        self,
        email: str,
        timeout: int = 120,
        poll_interval: int = 5,
    ) -> Optional[str]:
        """
        Poll the inbox until a ChatGPT verification email arrives or *timeout*
        seconds elapse.  Returns the verification URL (or code) if found,
        otherwise ``None``.
        """
        logger.info("Waiting up to %ds for verification email at %s …", timeout, email)
        deadline = time.time() + timeout

        while time.time() < deadline:
            link = self._check_inbox(email)
            if link:
                logger.info("Verification link obtained.")
                return link
            time.sleep(poll_interval)

        logger.warning("Timed out waiting for verification email.")
        return None

    def _check_inbox(self, email: str) -> Optional[str]:
        """Check the inbox once and return a verification link if found."""
        if config.EMAIL_PROVIDER == "tempmail":
            return self._check_guerrilla_inbox(email)
        if config.EMAIL_PROVIDER in ("gmail", "custom"):
            return self._check_imap_inbox(email)
        return None

    def _check_guerrilla_inbox(self, email: str) -> Optional[str]:
        try:
            import requests

            resp = requests.get(
                "https://api.guerrillamail.com/ajax.php",
                params={"f": "get_email_list", "offset": "0"},
                timeout=10,
            )
            resp.raise_for_status()
            messages = resp.json().get("list", [])
            for msg in messages:
                if "openai" in msg.get("mail_from", "").lower() or "openai" in msg.get(
                    "mail_subject", ""
                ).lower():
                    mail_id = msg["mail_id"]
                    detail = requests.get(
                        "https://api.guerrillamail.com/ajax.php",
                        params={"f": "fetch_email", "email_id": mail_id},
                        timeout=10,
                    ).json()
                    body = detail.get("mail_body", "")
                    return self._extract_verification_link(body)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Guerrilla Mail inbox check failed: %s", exc)
        return None

    def _check_imap_inbox(self, email: str) -> Optional[str]:
        """Check a real IMAP inbox for a verification email."""
        try:
            if config.EMAIL_PROVIDER == "gmail":
                host, port = "imap.gmail.com", 993
                username, password = config.GMAIL_USERNAME, config.GMAIL_PASSWORD
            else:
                host, port = config.SMTP_HOST, 993
                username, password = config.SMTP_USER, config.SMTP_PASS

            with imaplib.IMAP4_SSL(host, port) as mail:
                mail.login(username, password)
                mail.select("inbox")
                _, data = mail.search(None, '(FROM "openai.com" UNSEEN)')
                for num in reversed(data[0].split()):
                    _, msg_data = mail.fetch(num, "(RFC822)")
                    raw = msg_data[0][1]  # type: ignore[index]
                    import email as email_lib

                    msg = email_lib.message_from_bytes(raw)
                    body = self._get_email_body(msg)
                    link = self._extract_verification_link(body)
                    if link:
                        return link
        except Exception as exc:  # noqa: BLE001
            logger.debug("IMAP inbox check failed: %s", exc)
        return None

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_email_body(msg) -> str:  # type: ignore[no-untyped-def]
        """Extract plain text or HTML body from an email.Message object."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ("text/plain", "text/html"):
                    return part.get_payload(decode=True).decode(errors="replace")
        return msg.get_payload(decode=True).decode(errors="replace")  # type: ignore[union-attr]

    @staticmethod
    def _extract_verification_link(body: str) -> Optional[str]:
        """Return the first OpenAI verification link found in *body*."""
        pattern = r"https://[^\s\"'>]*openai\.com[^\s\"'>]*/verify[^\s\"'><]+"
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(0)
        # Fallback: any https link from openai
        match = re.search(r"https://[^\s\"'>]*openai\.com[^\s\"'><]+", body, re.IGNORECASE)
        return match.group(0) if match else None

    # ------------------------------------------------------------------ #
    # SMTP sending (optional / utility)                                    #
    # ------------------------------------------------------------------ #

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send a plain-text email via the configured SMTP server."""
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = config.SMTP_USER
            msg["To"] = to

            if config.SMTP_SECURE:
                with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
                    smtp.login(config.SMTP_USER, config.SMTP_PASS)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as smtp:
                    smtp.starttls()
                    smtp.login(config.SMTP_USER, config.SMTP_PASS)
                    smtp.send_message(msg)

            logger.info("Email sent to %s", to)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email to %s: %s", to, exc)
            return False
