"""python-eol checks if the current running python version is (close) to end of life."""
from __future__ import annotations

import argparse
import json
import logging
import platform
from datetime import date
from pathlib import Path
from typing import Any

from ._docker_utils import _extract_python_version_from_docker_file, _find_docker_files

EOL_WARN_DAYS = 60

logger = logging.getLogger(__name__)


def _get_major_minor() -> str:
    major, minor, patch = platform.python_version_tuple()
    return f"{major}.{minor}"


def _get_db_file_path(*, nep_mode: bool = False) -> Path:
    major, minor, _ = platform.python_version_tuple()
    filename = "db.json" if not nep_mode else "db_nep.json"
    if int(major) == 3 and int(minor) >= 9:  # noqa: PLR2004
        import importlib.resources

        data_path = importlib.resources.files("python_eol")
        db_file = f"{data_path}/{filename}"
    else:
        import pkg_resources  # pragma: no cover

        db_file = pkg_resources.resource_filename(
            "python_eol",
            filename,
        )  # pragma: no cover

    return Path(db_file)


def _check_eol(
    python_version: str,
    version_info: dict[str, dict[str, Any]],
    *,
    fail_close_to_eol: bool = False,
    prefix: str = "",
) -> int:
    my_version_info = version_info[python_version]
    today = date.today()
    eol_date = date.fromisoformat(my_version_info["End of Life"])
    time_to_eol = eol_date - today

    if time_to_eol.days < 0:
        logger.error(f"{prefix}Python {python_version} is beyond end of life")
        return 1
    if time_to_eol.days < EOL_WARN_DAYS:
        msg = (
            f"{prefix}Python {python_version} is going to "
            f"be end of life within the next 2 months ({eol_date})"
        )

        if fail_close_to_eol:
            logger.error(msg)
            return 1
        else:
            logger.warning(msg)
            return 0
    return 0


def _check_python_eol(
    *,
    fail_close_to_eol: bool = False,
    check_docker_files: bool = False,
    nep_mode: bool = False,
) -> int:
    db_file = _get_db_file_path(nep_mode=nep_mode)
    with db_file.open() as f:
        eol_data = json.load(f)

    version_info = {entry["Version"]: entry for entry in eol_data}

    my_version = _get_major_minor()

    docker_res = 0
    if check_docker_files:
        for path in _find_docker_files():
            version = _extract_python_version_from_docker_file(path)
            if version:
                docker_res = (
                    _check_eol(
                        version,
                        version_info,
                        fail_close_to_eol=fail_close_to_eol,
                        prefix=f"{path}: ",
                    )
                    or docker_res
                )
    return (
        _check_eol(my_version, version_info, fail_close_to_eol=fail_close_to_eol)
        or docker_res
    )


def _get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="eol check if your python version is beyond end of life",
    )
    parser.add_argument(
        "--fail-close-to-eol",
        action="store_true",
        help="Fail if the python version is close to eol instead of just warn",
    )
    parser.add_argument(
        "--check-docker-files",
        action="store_true",
        help=(
            "Search for Dockerfile (**/*Dockerfile*) and check "
            "the python versions specified inside them"
        ),
    )
    parser.add_argument(
        "--nep29",
        action="store_true",
        help=("Use NEP0029 end of life policy"),
    )
    return parser


def main() -> int:
    """Run main entry point."""
    parser = _get_argparser()
    args, unknown_args = parser.parse_known_args()
    return _check_python_eol(
        fail_close_to_eol=args.fail_close_to_eol,
        check_docker_files=args.check_docker_files,
        nep_mode=args.nep29,
    )


if __name__ == "__main__":
    raise SystemExit(main())
