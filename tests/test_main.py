import logging
import sys
from pathlib import Path
from typing import Iterable
from unittest import mock

import pytest
from freezegun import freeze_time

from python_eol.main import _check_python_eol, _get_argparser, main

skip_py37 = pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="Skip python 3.7 due to incompatibility",
)

skip_py38 = pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="Skip python 3.8 due to incompatibility",
)


@pytest.fixture()
def _mock_py37() -> Iterable[None]:
    with mock.patch("platform.python_version_tuple") as mocked_python_version_tuple:
        mocked_python_version_tuple.return_value = (3, 7, 0)
        yield


mock_py37 = pytest.mark.usefixtures("_mock_py37")


@pytest.fixture()
def _mock_py311() -> Iterable[None]:
    with mock.patch("platform.python_version_tuple") as mocked_python_version_tuple:
        mocked_python_version_tuple.return_value = (3, 11, 0)
        yield


mock_py311 = pytest.mark.usefixtures("_mock_py311")


def test_get_argparser() -> None:
    parser = _get_argparser()
    args, kwargs = parser.parse_known_args(
        ["--fail-close-to-eol"],
    )

    assert args.fail_close_to_eol is True


def test_get_argparser2() -> None:
    parser = _get_argparser()
    args, kwargs = parser.parse_known_args(
        [],
    )

    assert args.fail_close_to_eol is False


@mock_py37
@freeze_time("2023-04-30")
@pytest.mark.parametrize("fail_close_to_eol", [True, False])
def test_check_python_eol(
    fail_close_to_eol: bool,
) -> None:
    result = _check_python_eol(fail_close_to_eol=fail_close_to_eol)
    if fail_close_to_eol:
        assert result == 1
    else:
        assert result == 0


@mock_py37
@freeze_time("2023-06-28")  # python 3.7 eol is 2023-06-27
def test_version_beyond_eol() -> None:
    assert _check_python_eol() == 1


@skip_py37
@skip_py38
@mock_py311
@freeze_time("2023-06-28")  # python 3.11 eol is 2027-10-24
def test_version_far_from_eol() -> None:
    assert _check_python_eol() == 0


@skip_py37
@skip_py38
@mock_py311
@freeze_time("2023-06-28")  # python 3.11 eol is 2027-10-24
def test_main() -> None:
    assert main() == 0


@skip_py37
@skip_py38
@mock_py311
@freeze_time("2023-06-28")  # python 3.7 eol is 2023-06-27
def test_version_in_dockerfile_errors(
    tmpdir: Path,
) -> None:
    with mock.patch("python_eol.main._find_docker_files") as mocked_find_docker_files:
        p = Path(tmpdir / "Dockerfile")
        p.write_text("FROM python:3.7")
        mocked_find_docker_files.return_value = [p]
        assert _check_python_eol(check_docker_files=True) == 1


@skip_py37
@skip_py38
@mock_py311
@freeze_time("2023-06-22")  # python 3.7 eol is 2023-06-27
@pytest.mark.parametrize(
    ("fail_close_to_eol", "expected_return_status", "log_level"),
    [(True, 1, logging.ERROR), (False, 0, logging.WARNING)],
)
def test_version_in_dockerfile_close_to_eol(
    tmpdir: Path,
    fail_close_to_eol: bool,
    expected_return_status: int,
    log_level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with mock.patch("python_eol.main._find_docker_files") as mocked_find_docker_files:
        p = Path(tmpdir / "Dockerfile")
        p.write_text("FROM python:3.7")
        mocked_find_docker_files.return_value = [p]
        result = _check_python_eol(
            fail_close_to_eol=fail_close_to_eol,
            check_docker_files=True,
        )
        assert result == expected_return_status

    msg = f"{p}: Python 3.7 is going to be end of life in 2 months 2023-06-27"
    assert caplog.record_tuples == [("python_eol.main", log_level, msg)]
