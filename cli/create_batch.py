"""
CLI command – create a batch of ChatGPT accounts.

Usage:
    python cli/create_batch.py <count>
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.account_creator import AccountCreator
from database.db_manager import db
from utils.logger import get_logger

logger = get_logger("cli.create_batch")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python cli/create_batch.py <count>")
        sys.exit(1)

    try:
        count = int(sys.argv[1])
        if count < 1:
            raise ValueError
    except ValueError:
        print("Error: <count> must be a positive integer.")
        sys.exit(1)

    db.initialize()
    creator = AccountCreator()

    logger.info("Starting batch creation of %d accounts …", count)
    results = creator.create_batch_accounts(count)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n{'─' * 40}")
    print(f"  Batch complete: {len(successful)}/{count} successful")
    print(f"{'─' * 40}")
    for r in results:
        status = "✅" if r["success"] else "❌"
        info = r.get("email", "unknown")
        print(f"  {status} {info}")
    print(f"{'─' * 40}\n")

    db.close()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
