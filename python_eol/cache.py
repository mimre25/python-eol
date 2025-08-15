"""Cache management for python-eol."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import appdirs
import requests

logger = logging.getLogger(__name__)

CACHE_DIR = Path(appdirs.user_cache_dir("python-eol"))
CACHE_EXPIRY = timedelta(days=31)


def _get_cache_file(*, nep_mode: bool) -> Path:
    """Get the cache file path."""
    if nep_mode:
        return CACHE_DIR / "eol_data_nep.json"
    return CACHE_DIR / "eol_data.json"


def _fetch_eol_data(*, nep_mode: bool) -> list[dict[str, Any]] | None:
    """Fetch EOL data from the API."""
    if nep_mode:
        api_url = (
            "https://raw.githubusercontent.com/scientific-python/specs/main/spec-0000/"
            "python-support.json"
        )
    else:
        api_url = "https://endoflife.date/api/python.json"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        raw_data = response.json()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch EOL data: {e}")
        return None

    processed_data: list[dict[str, Any]] = []
    if nep_mode:
        data = cast("dict[str, Any]", raw_data)
        releases = cast("list[dict[str, Any]]", data.get("releases", []))
        for entry in releases:
            end_of_life_date = datetime.strptime(
                entry["eol"],
                "%Y-%m-%d",
            ).date()
            entry_data = {
                "Version": entry["version"],
                "End of Life": str(end_of_life_date),
            }
            processed_data.append(entry_data)
    else:
        eol_data = cast("list[dict[str, Any]]", raw_data)
        for entry in eol_data:
            raw_version = entry["latest"]
            major_minor_parts = raw_version.split(".")[:2]
            parsed_version = ".".join(major_minor_parts)
            end_of_life_date = datetime.strptime(entry["eol"], "%Y-%m-%d").date()
            entry_data = {
                "Version": parsed_version,
                "End of Life": str(end_of_life_date),
            }
            processed_data.append(entry_data)
    return processed_data


def _read_cache(*, nep_mode: bool) -> list[dict[str, Any]] | None:
    """Read EOL data from cache."""
    cache_file = _get_cache_file(nep_mode=nep_mode)
    if not cache_file.exists():
        return None

    if (
        datetime.fromtimestamp(cache_file.stat().st_mtime)
        < datetime.now() - CACHE_EXPIRY
    ):
        logger.debug("Cache is expired.")
        return None

    try:
        with cache_file.open() as f:
            data = json.load(f)
            return cast("list[dict[str, Any]]", data)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to read cache: {e}")
        return None


def _write_cache(data: list[dict[str, Any]], *, nep_mode: bool) -> None:
    """Write EOL data to cache."""
    cache_file = _get_cache_file(nep_mode=nep_mode)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w") as f:
            json.dump(data, f, indent=4)
    except OSError as e:
        logger.warning(f"Failed to write cache: {e}")


def get_eol_data(*, nep_mode: bool) -> list[dict[str, Any]] | None:
    """Get EOL data from cache or fetch if stale."""
    cached_data = _read_cache(nep_mode=nep_mode)
    if cached_data:
        logger.debug("Using cached EOL data.")
        return cached_data

    logger.debug("Fetching new EOL data.")
    fetched_data = _fetch_eol_data(nep_mode=nep_mode)
    if fetched_data:
        _write_cache(fetched_data, nep_mode=nep_mode)
        return fetched_data

    return None
