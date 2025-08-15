"""Cache management for python-eol."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import appdirs
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CACHE_DIR = Path(appdirs.user_cache_dir("python-eol"))
CACHE_FILE = CACHE_DIR / "eol_data.json"
CACHE_FILE_NEP = CACHE_DIR / "eol_data_nep.json"
CACHE_EXPIRY = timedelta(days=31)


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


def _fetch_nep_data() -> list[dict[str, Any]] | None:
    """Fetch NEP 29 EOL data."""
    url = "https://numpy.org/neps/nep-0029-deprecation_policy.html#support-table"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch NEP data: {e}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")

    data = []
    for row in table.find_all("tr")[1:]:
        columns = row.find_all("td")
        end_of_life = columns[0].text.strip()
        version = columns[1].text.strip().rstrip("+")
        version_number = version.split(".")
        version_number[-1] = str(int(version_number[-1]) - 1)
        parsed_version = ".".join(version_number)
        end_of_life_date = datetime.strptime(end_of_life, "%b %d, %Y").date()

        existing_data = next((d for d in data if d["Version"] == parsed_version), None)
        if existing_data:
            existing_data["End of Life"] = min(
                existing_data["End of Life"],
                str(end_of_life_date),
            )
        else:
            row_data = {"Version": parsed_version, "End of Life": str(end_of_life_date)}
            data.append(row_data)
    return data


def _read_cache(*, nep_mode: bool = False) -> list[dict[str, Any]] | None:
    """Read EOL data from cache."""
    cache_file = CACHE_FILE_NEP if nep_mode else CACHE_FILE
    if not cache_file.exists():
        return None

    if datetime.fromtimestamp(cache_file.stat().st_mtime) < datetime.now() - CACHE_EXPIRY:
        logger.debug("Cache is expired.")
        return None

    try:
        with cache_file.open() as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to read cache: {e}")
        return None


def _write_cache(data: list[dict[str, Any]], *, nep_mode: bool = False) -> None:
    """Write EOL data to cache."""
    cache_file = CACHE_FILE_NEP if nep_mode else CACHE_FILE
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        logger.warning(f"Failed to write cache: {e}")


def get_eol_data(*, nep_mode: bool = False) -> list[dict[str, Any]] | None:
    """Get EOL data from cache or fetch if stale."""
    cached_data = _read_cache(nep_mode=nep_mode)
    if cached_data:
        logger.debug("Using cached EOL data.")
        return cached_data

    logger.debug("Fetching new EOL data.")
    fetch_function = _fetch_nep_data if nep_mode else _fetch_eol_data
    fetched_data = fetch_function()
    if fetched_data:
        _write_cache(fetched_data, nep_mode=nep_mode)
        return fetched_data

    return None
