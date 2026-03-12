"""
Account creator – orchestrates browser automation with Playwright to
register new ChatGPT accounts.
"""

import random
import string
import time
from typing import Any, Dict, List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import config
from core.email_manager import EmailManager
from database.db_manager import db
from utils.logger import get_logger

logger = get_logger("account_creator")


def _random_password(length: int = 16) -> str:
    """Generate a secure random password."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.SystemRandom().choice(chars) for _ in range(length))


class AccountCreationError(Exception):
    """Raised when account creation fails after all retries."""


class AccountCreator:
    """
    Creates ChatGPT accounts using Playwright browser automation.

    Usage::

        creator = AccountCreator()
        result = creator.create_single_account()
        print(result)
    """

    def __init__(self) -> None:
        self._email_manager = EmailManager()
        self._creation_count = 0  # simple in-process rate counter

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def create_single_account(self) -> Dict[str, Any]:
        """Create one account and return a result dict."""
        self._enforce_rate_limit()
        email = self._email_manager.generate_email()
        password = _random_password()

        logger.info("Creating account: %s", email)
        account_id = db.save_account(email, password)

        try:
            self._run_browser_flow(email, password, account_id)
            result: Dict[str, Any] = {
                "success": True,
                "email": email,
                "password": password,
                "account_id": account_id,
            }
            db.update_account_status(account_id, "created", verified=True)
            db.add_log("create_account", "success", account_id)
            logger.info("Account created successfully: %s", email)
        except Exception as exc:  # noqa: BLE001
            db.update_account_status(account_id, "failed")
            db.add_log("create_account", "failed", account_id, str(exc))
            logger.error("Account creation failed for %s: %s", email, exc)
            result = {"success": False, "email": email, "error": str(exc)}

        self._creation_count += 1
        return result

    def create_batch_accounts(self, count: int) -> List[Dict[str, Any]]:
        """Create *count* accounts sequentially with rate limiting."""
        if count < 1:
            raise ValueError("count must be >= 1")

        logger.info("Starting batch creation of %d accounts …", count)
        results: List[Dict[str, Any]] = []

        for i in range(count):
            logger.info("Batch progress: %d/%d", i + 1, count)
            result = self.create_single_account()
            results.append(result)

            if i < count - 1:
                logger.debug("Waiting %ds before next account …", config.DELAY_BETWEEN)
                time.sleep(config.DELAY_BETWEEN)

        successful = sum(1 for r in results if r["success"])
        logger.info(
            "Batch complete. %d/%d accounts created successfully.", successful, count
        )
        return results

    def interactive_mode(self) -> None:
        """Simple interactive prompt for manual use."""
        print("ChatGPT Account Creator – interactive mode")
        print("  [1] Create single account")
        print("  [2] Create batch of accounts")
        print("  [q] Quit")

        while True:
            choice = input("\nSelect option: ").strip().lower()
            if choice == "1":
                result = self.create_single_account()
                print(f"\nResult: {result}")
            elif choice == "2":
                try:
                    n = int(input("How many accounts? ").strip())
                    results = self.create_batch_accounts(n)
                    for r in results:
                        print(r)
                except ValueError:
                    print("Please enter a valid number.")
            elif choice == "q":
                break
            else:
                print("Unknown option.")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _enforce_rate_limit(self) -> None:
        """Raise if the per-day limit has been reached."""
        if self._creation_count >= config.RATE_LIMIT_PER_DAY:
            raise AccountCreationError(
                f"Daily rate limit of {config.RATE_LIMIT_PER_DAY} accounts reached."
            )

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        reraise=True,
    )
    def _run_browser_flow(
        self, email: str, password: str, account_id: int
    ) -> None:
        """
        Launch a Playwright browser and walk through the ChatGPT sign-up form.

        The flow is wrapped in a tenacity retry so transient failures (network
        hiccups, slow page loads) are retried automatically up to three times.
        """
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        proxy_settings: Optional[Dict[str, str]] = None
        if config.PROXY_ENABLED and config.PROXY_URL:
            proxy_settings = {"server": config.PROXY_URL}
            if config.PROXY_USERNAME:
                proxy_settings["username"] = config.PROXY_USERNAME
                proxy_settings["password"] = config.PROXY_PASSWORD

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=config.HEADLESS,
                slow_mo=config.SLOW_MO,
                proxy=proxy_settings,  # type: ignore[arg-type]
            )
            context = browser.new_context(
                user_agent=config.USER_AGENT,
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.set_default_timeout(config.TIMEOUT)

            try:
                logger.debug("Navigating to sign-up page …")
                page.goto(config.SIGNUP_URL)

                # --- Click "Sign up" if present on the landing page ---
                signup_btn = page.query_selector("text=Sign up")
                if signup_btn:
                    signup_btn.click()
                    page.wait_for_load_state("networkidle")

                # --- Fill in the email field ---
                page.fill("input[name='email'], input[type='email']", email)
                page.keyboard.press("Enter")
                page.wait_for_load_state("networkidle")

                # --- Fill in the password field ---
                page.fill("input[name='password'], input[type='password']", password)
                page.keyboard.press("Enter")
                page.wait_for_load_state("networkidle")

                # --- Handle email verification ---
                db.add_log("email_verification", "pending", account_id)
                verification_link = self._email_manager.wait_for_verification_email(
                    email
                )
                if verification_link:
                    page.goto(verification_link)
                    page.wait_for_load_state("networkidle")
                    db.add_log("email_verification", "success", account_id)
                else:
                    db.add_log(
                        "email_verification",
                        "timeout",
                        account_id,
                        "No verification email received",
                    )
                    logger.warning(
                        "Verification email not received for %s; continuing.", email
                    )

            finally:
                context.close()
                browser.close()
