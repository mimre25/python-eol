"""Cache management for python-eol."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import appdirs
import requests

logger = logging.getLogger(__name__)

CACHE_DIR = Path(appdirs.user_cache_dir("python-eol"))
CACHE_FILE = CACHE_DIR / "eol_data.json"
CACHE_EXPIRY = timedelta(days=1)


def _fetch_eol_data() -> list[dict[str, Any]] | None:
    """Fetch EOL data from the API."""
    api_url = "https://endoflife.date/api/python.json"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch EOL data: {e}")
        return None

    processed_data = []
    for entry in data:
        raw_version = entry["latest"]
        major_minor_parts = raw_version.split(".")[:2]
        parsed_version = ".".join(major_minor_parts)
        end_of_life_date = datetime.strptime(entry["eol"], "%Y-%m-%d").date()
        entry_data = {"Version": parsed_version, "End of Life": str(end_of_life_date)}
        processed_data.append(entry_data)
    return processed_data


def _read_cache() -> list[dict[str, Any]] | None:
    """Read EOL data from cache."""
    if not CACHE_FILE.exists():
        return None

    if datetime.fromtimestamp(CACHE_FILE.stat().st_mtime) < datetime.now() - CACHE_EXPIRY:
        logger.debug("Cache is expired.")
        return None

    try:
        with CACHE_FILE.open() as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to read cache: {e}")
        return None


def _write_cache(data: list[dict[str, Any]]) -> None:
    """Write EOL data to cache."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with CACHE_FILE.open("w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        logger.warning(f"Failed to write cache: {e}")


def get_eol_data() -> list[dict[str, Any]] | None:
    """Get EOL data from cache or fetch if stale."""
    cached_data = _read_cache()
    if cached_data:
        logger.debug("Using cached EOL data.")
        return cached_data

    logger.debug("Fetching new EOL data.")
    fetched_data = _fetch_eol_data()
    if fetched_data:
        _write_cache(fetched_data)
        return fetched_data

    return None
