from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Generator
from unittest import mock

import pytest

if TYPE_CHECKING:
    from pathlib import Path
import requests
from freezegun import freeze_time

from python_eol.cache import (
    CACHE_EXPIRY,
    _fetch_eol_data,
    _read_cache,
    _write_cache,
    get_eol_data,
)

FAKE_EOL_DATA = [{"Version": "3.9", "End of Life": "2025-10-01"}]


@pytest.fixture
def mock_cache_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Mock the cache file and its directory."""
    cache_dir = tmp_path / "python-eol"
    cache_file = cache_dir / "eol_data.json"
    with mock.patch("python_eol.cache.CACHE_DIR", cache_dir), mock.patch(
        "python_eol.cache.CACHE_FILE",
        cache_file,
    ):
        yield cache_file


def test_fetch_eol_data_success() -> None:
    """Test fetching EOL data successfully."""
    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = [
            {"latest": "3.9.0", "eol": "2025-10-01"},
        ]
        data = _fetch_eol_data()
        assert data == FAKE_EOL_DATA


def test_fetch_eol_data_failure() -> None:
    """Test fetching EOL data with a request failure."""
    with mock.patch(
        "requests.get",
        side_effect=requests.RequestException("API is down"),
    ):
        data = _fetch_eol_data()
        assert data is None


def test_read_write_cache(mock_cache_file: Path) -> None:
    """Test writing to and reading from the cache."""
    _write_cache(FAKE_EOL_DATA)
    assert mock_cache_file.exists()
    with mock_cache_file.open() as f:
        data = json.load(f)
    assert data == FAKE_EOL_DATA

    read_data = _read_cache()
    assert read_data == FAKE_EOL_DATA


@pytest.mark.usefixtures("mock_cache_file")
def test_read_cache_expired() -> None:
    """Test that an expired cache returns None."""
    _write_cache(FAKE_EOL_DATA)
    with freeze_time(datetime.now() + CACHE_EXPIRY + CACHE_EXPIRY):
        assert _read_cache() is None


@pytest.mark.usefixtures("mock_cache_file")
def test_read_cache_not_found() -> None:
    """Test that a non-existent cache returns None."""
    assert _read_cache() is None


@pytest.mark.usefixtures("mock_cache_file")
def test_get_eol_data_from_cache() -> None:
    """Test get_eol_data reads from a valid cache."""
    _write_cache(FAKE_EOL_DATA)
    with mock.patch("python_eol.cache._fetch_eol_data") as mock_fetch:
        data = get_eol_data()
        mock_fetch.assert_not_called()
        assert data == FAKE_EOL_DATA


@pytest.mark.usefixtures("mock_cache_file")
def test_get_eol_data_fetches_when_cache_is_stale() -> None:
    """Test get_eol_data fetches new data when cache is stale."""
    _write_cache(FAKE_EOL_DATA)
    with freeze_time(
        datetime.now() + CACHE_EXPIRY + CACHE_EXPIRY,
    ), mock.patch("python_eol.cache._fetch_eol_data") as mock_fetch:
        mock_fetch.return_value = [{"Version": "3.10", "End of Life": "2026-10-01"}]
        data = get_eol_data()
        mock_fetch.assert_called_once()
        assert data == [{"Version": "3.10", "End of Life": "2026-10-01"}]


@pytest.mark.usefixtures("mock_cache_file")
def test_get_eol_data_fetches_when_no_cache() -> None:
    """Test get_eol_data fetches new data when no cache exists."""
    with mock.patch("python_eol.cache._fetch_eol_data") as mock_fetch:
        mock_fetch.return_value = FAKE_EOL_DATA
        data = get_eol_data()
        mock_fetch.assert_called_once()
        assert data == FAKE_EOL_DATA
