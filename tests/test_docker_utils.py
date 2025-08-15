from __future__ import annotations

from pathlib import Path

import pytest

from python_eol._docker_utils import (
    _extract_python_version_from_docker_file,
    _find_docker_files,
)


def test_find_docker_files(tmpdir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmpdir)
    p = Path("Dockerfile")
    p.touch()
    d = Path("a/b")
    d.mkdir(parents=True)
    p2 = d / "Dockerfile-test"
    p2.touch()
    assert sorted(_find_docker_files()) == sorted([p, p2])


@pytest.mark.parametrize(
    ("content", "py_version"),
    [
        ("FROM python:3.7", "3.7"),
        ("FROM python:3.8-buster", "3.8"),
        ("FROM python:3.9.16-slim", "3.9"),
        ("FROM python:3.10-alpine3.16", "3.10"),
        ("FROM python:3.11.3-windowsservercore-1809", "3.11"),
        ("FROM python:3.12-rc-bullseye", "3.12"),
        ("FROM python:3.12.0a7-bullseye", "3.12"),
        ("FROM python:latest", None),  # latest is ignored as it's not eol
        ("FROM ubuntu:latest", None),
        (
            "FROM ubuntu:latest\n\napt install python=3.7\n",
            None,
        ),  # ensure other comments don't get erronously picked up
    ],
)
def test_extract_python_version_from_docker_file(
    content: str,
    py_version: str | None,
    tmpdir: Path,
) -> None:
    p = Path(tmpdir / "Dockerfile")
    p.write_text(f"{content}\n")

    assert _extract_python_version_from_docker_file(p) == py_version
