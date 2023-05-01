from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

# ignoring 'latest' with this regex, as 'latest' usually isn't eol
PYTHON_VERSION_DOCKER_REGEX = re.compile(r"^FROM python:(\d.\d\d?).*")


def _find_docker_files() -> Iterable[Path]:
    return list(Path(".").glob("**/*Dockerfile*"))


def _extract_python_version_from_docker_file(filename: Path) -> str | None:
    with filename.open() as f:
        lines = f.readlines()

    for line in lines:
        res = PYTHON_VERSION_DOCKER_REGEX.match(line)
        if res:
            version = res.group(1)
            return version
    return None
