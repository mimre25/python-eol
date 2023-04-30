import sys
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


@pytest.mark.parametrize("fail_close_to_eol", [True, False])
@mock.patch("platform.python_version_tuple")
@freeze_time("2023-04-30")
def test_check_python_eol(
    mocked_python_version_tuple: mock.MagicMock,
    *,
    fail_close_to_eol: bool,
) -> None:
    mocked_python_version_tuple.return_value = (3, 7, 0)
    result = _check_python_eol(fail_close_to_eol=fail_close_to_eol)
    if fail_close_to_eol:
        assert result == 1
    else:
        assert result == 0


@mock.patch("platform.python_version_tuple")
@freeze_time("2023-06-28")  # python 3.7 eol is 2023-06-27
def test_version_beyond_eol(
    mocked_python_version_tuple: mock.MagicMock,
) -> None:
    mocked_python_version_tuple.return_value = (3, 7, 0)
    assert _check_python_eol() == 1


@skip_py37
@skip_py38
@mock.patch("platform.python_version_tuple")
@freeze_time("2023-06-28")  # python 3.11 eol is 2027-10-24
def test_version_far_from_eol(
    mocked_python_version_tuple: mock.MagicMock,
) -> None:
    mocked_python_version_tuple.return_value = (3, 11, 0)
    assert _check_python_eol() == 0


@skip_py37
@skip_py38
@mock.patch("platform.python_version_tuple")
@freeze_time("2023-06-28")  # python 3.11 eol is 2027-10-24
def test_main(
    mocked_python_version_tuple: mock.MagicMock,
) -> None:
    mocked_python_version_tuple.return_value = (3, 11, 0)
    assert main() == 0
