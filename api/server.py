"""
FastAPI REST server for the ChatGPT Account Creator Bot.

Run with:
    python api/server.py
or:
    uvicorn api.server:app --host 0.0.0.0 --port 3000
"""

import sys
import os

# Allow imports from the project root when this file is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import config
from core.account_creator import AccountCreator
from database.db_manager import db
from utils.logger import get_logger

logger = get_logger("api_server")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    db.initialize()
    logger.info("Database initialised.")
    yield
    db.close()
    logger.info("Database connection closed.")


app = FastAPI(
    title="ChatGPT Account Creator API",
    description="REST API for automated ChatGPT account creation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
# Lazy-initialised singletons                                          #
# ------------------------------------------------------------------ #

_account_creator: Optional[AccountCreator] = None


def get_account_creator() -> AccountCreator:
    global _account_creator  # noqa: PLW0603
    if _account_creator is None:
        _account_creator = AccountCreator()
    return _account_creator


# ------------------------------------------------------------------ #
# Request / response models                                            #
# ------------------------------------------------------------------ #


class BatchRequest(BaseModel):
    count: int


# ------------------------------------------------------------------ #
# Endpoints                                                            #
# ------------------------------------------------------------------ #


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    from datetime import datetime

    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/create-account")
async def create_account() -> Dict[str, Any]:
    """Create a single ChatGPT account."""
    logger.info("API request: create single account")
    result = get_account_creator().create_single_account()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


@app.post("/api/create-batch")
async def create_batch(body: BatchRequest) -> Dict[str, Any]:
    """Create a batch of ChatGPT accounts."""
    if body.count < 1:
        raise HTTPException(status_code=400, detail="count must be >= 1")
    logger.info("API request: create batch of %d accounts", body.count)
    results: List[Dict[str, Any]] = get_account_creator().create_batch_accounts(body.count)
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
        },
    }


@app.get("/api/accounts")
async def get_accounts() -> Dict[str, Any]:
    """Return all stored accounts."""
    accounts = db.get_all_accounts()
    return {"accounts": accounts, "total": len(accounts)}


@app.get("/api/accounts/{email}")
async def get_account(email: str) -> Dict[str, Any]:
    """Return a single account by email address."""
    account = db.get_account_by_email(email)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.server:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
    )
