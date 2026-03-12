"""
CLI command – create a single ChatGPT account.

Usage:
    python cli/create_account.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.account_creator import AccountCreator
from database.db_manager import db
from utils.logger import get_logger

logger = get_logger("cli.create_account")


def main() -> None:
    db.initialize()
    creator = AccountCreator()

    logger.info("Creating a single account …")
    result = creator.create_single_account()

    if result["success"]:
        print(f"\n✅ Account created successfully!")
        print(f"   Email   : {result['email']}")
        print(f"   Password: {result['password']}")
        print(f"   ID      : {result['account_id']}")
    else:
        print(f"\n❌ Account creation failed: {result.get('error')}")
        sys.exit(1)

    db.close()


if __name__ == "__main__":
    main()
