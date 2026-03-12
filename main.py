"""
Entry point for the ChatGPT Account Creator Bot.

Usage:
    python main.py --single
    python main.py --batch 5
"""

import argparse
import sys

from config import config
from core.account_creator import AccountCreator
from database.db_manager import db
from utils.logger import get_logger

logger = get_logger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ChatGPT Account Creator Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --single          Create one account
  python main.py --batch 5         Create five accounts
  python main.py                   Launch interactive mode
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--single", action="store_true", help="Create a single account"
    )
    group.add_argument(
        "--batch",
        metavar="COUNT",
        type=int,
        help="Create COUNT accounts in batch mode",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info("Initialising ChatGPT Account Creator Bot …")
    db.initialize()
    logger.info("Database initialised.")

    creator = AccountCreator()

    try:
        if args.single:
            logger.info("Mode: single account creation")
            result = creator.create_single_account()
            if result["success"]:
                logger.info(
                    "Account created – email: %s, id: %s",
                    result["email"],
                    result["account_id"],
                )
            else:
                logger.error("Account creation failed: %s", result.get("error"))
                sys.exit(1)

        elif args.batch:
            logger.info("Mode: batch creation (%d accounts)", args.batch)
            results = creator.create_batch_accounts(args.batch)
            successful = sum(1 for r in results if r["success"])
            logger.info(
                "Batch complete: %d/%d accounts created.", successful, args.batch
            )
            if successful < args.batch:
                sys.exit(1)

        else:
            logger.info("Mode: interactive")
            creator.interactive_mode()

    finally:
        db.close()


if __name__ == "__main__":
    main()
