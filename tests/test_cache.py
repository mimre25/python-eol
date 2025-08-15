from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Iterator
from unittest import mock

if TYPE_CHECKING:
    from pathlib import Path

import pytest
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
FAKE_EOL_DATA_NEP = [{"Version": "3.8", "End of Life": "2023-10-01"}]


@pytest.fixture
def mock_cache_file(tmp_path: Path) -> Iterator[Path]:
    """Mock the cache file and its directory."""
    cache_dir = tmp_path / "python-eol"
    cache_file = cache_dir / "eol_data.json"
    with mock.patch("python_eol.cache.CACHE_DIR", cache_dir):
        yield cache_file


@pytest.fixture
def mock_cache_file_nep(tmp_path: Path) -> Iterator[Path]:
    """Mock the NEP mode cache file and its directory."""
    cache_dir = tmp_path / "python-eol"
    cache_file = cache_dir / "eol_data_nep.json"
    with mock.patch("python_eol.cache.CACHE_DIR", cache_dir):
        yield cache_file


def test_fetch_eol_data_success() -> None:
    """Test fetching EOL data successfully."""
    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = [
            {"latest": "3.9.0", "eol": "2025-10-01"},
        ]
        data = _fetch_eol_data(nep_mode=False)
        assert data == FAKE_EOL_DATA


def test_fetch_eol_data_success_nep() -> None:
    """Test fetching EOL data successfully for NEP mode."""
    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "releases": [{"version": "3.8", "eol": "2023-10-01"}],
        }
        data = _fetch_eol_data(nep_mode=True)
        assert data == FAKE_EOL_DATA_NEP


def test_fetch_eol_data_failure() -> None:
    """Test fetching EOL data with a request failure."""
    with mock.patch(
        "requests.get",
        side_effect=requests.RequestException("API is down"),
    ):
        data = _fetch_eol_data(nep_mode=False)
        assert data is None


def test_read_write_cache(mock_cache_file: Path) -> None:
    """Test writing to and reading from the cache."""
    _write_cache(FAKE_EOL_DATA, nep_mode=False)
    assert mock_cache_file.exists()
    with mock_cache_file.open() as f:
        data = json.load(f)
    assert data == FAKE_EOL_DATA
    read_data = _read_cache(nep_mode=False)
    assert read_data == FAKE_EOL_DATA


def test_read_write_cache_nep(mock_cache_file_nep: Path) -> None:
    """Test writing to and reading from the cache for NEP mode."""
    _write_cache(FAKE_EOL_DATA_NEP, nep_mode=True)
    assert mock_cache_file_nep.exists()
    with mock_cache_file_nep.open() as f:
        data = json.load(f)
    assert data == FAKE_EOL_DATA_NEP
    read_data = _read_cache(nep_mode=True)
    assert read_data == FAKE_EOL_DATA_NEP


@pytest.mark.usefixtures("mock_cache_file")
def test_read_cache_expired() -> None:
    """Test that an expired cache returns None."""
    _write_cache(FAKE_EOL_DATA, nep_mode=False)
    with freeze_time(datetime.now() + CACHE_EXPIRY + CACHE_EXPIRY):
        assert _read_cache(nep_mode=False) is None


@pytest.mark.usefixtures("mock_cache_file")
def test_read_cache_not_found() -> None:
    """Test that a non-existent cache returns None."""
    assert _read_cache(nep_mode=False) is None


@pytest.mark.usefixtures("mock_cache_file")
def test_get_eol_data_from_cache() -> None:
    """Test get_eol_data reads from a valid cache."""
    _write_cache(FAKE_EOL_DATA, nep_mode=False)
    with mock.patch("python_eol.cache._fetch_eol_data") as mock_fetch:
        data = get_eol_data(nep_mode=False)
        mock_fetch.assert_not_called()
        assert data == FAKE_EOL_DATA


@pytest.mark.usefixtures("mock_cache_file_nep")
def test_get_eol_data_from_cache_nep() -> None:
    """Test get_eol_data reads from a valid cache for NEP mode."""
    _write_cache(FAKE_EOL_DATA_NEP, nep_mode=True)
    with mock.patch("python_eol.cache._fetch_eol_data") as mock_fetch:
        data = get_eol_data(nep_mode=True)
        mock_fetch.assert_not_called()
        assert data == FAKE_EOL_DATA_NEP


@pytest.mark.usefixtures("mock_cache_file")
def test_get_eol_data_fetches_when_cache_is_stale() -> None:
    """Test get_eol_data fetches new data when cache is stale."""
    _write_cache(FAKE_EOL_DATA, nep_mode=False)
    with freeze_time(
        datetime.now() + CACHE_EXPIRY + CACHE_EXPIRY,
    ), mock.patch("python_eol.cache._fetch_eol_data") as mock_fetch:
        mock_fetch.return_value = [
            {"Version": "3.10", "End of Life": "2026-10-01"},
        ]
        data = get_eol_data(nep_mode=False)
        mock_fetch.assert_called_once_with(nep_mode=False)
        assert data == [{"Version": "3.10", "End of Life": "2026-10-01"}]


@pytest.mark.usefixtures("mock_cache_file")
def test_get_eol_data_fetches_when_no_cache() -> None:
    """Test get_eol_data fetches new data when no cache exists."""
    with mock.patch("python_eol.cache._fetch_eol_data") as mock_fetch:
        mock_fetch.return_value = FAKE_EOL_DATA
        data = get_eol_data(nep_mode=False)
        mock_fetch.assert_called_once_with(nep_mode=False)
        assert data == FAKE_EOL_DATA
