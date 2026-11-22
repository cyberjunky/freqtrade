"""
Detect storage failures (disk full, read-only, I/O errors, locked database) and report free disk
space, so the bot can pause instead of trading with a database it cannot write to.
"""

import errno
import logging
import shutil
from pathlib import Path

from sqlalchemy.engine import make_url

from freqtrade.constants import Config


logger = logging.getLogger(__name__)

# Lower-case fragments of the messages SQLite / PostgreSQL / the OS give for storage problems.
STORAGE_ERROR_MARKERS: dict[str, str] = {
    "database or disk is full": "disk is full",
    "no space left on device": "disk is full",
    "could not extend file": "disk is full",
    "disk quota exceeded": "disk quota exceeded",
    "disk i/o error": "disk I/O error",
    "attempt to write a readonly database": "database is read-only",
    "read-only file system": "file system is read-only",
    "database is locked": "database is locked by another process",
    "unable to open database file": "database file cannot be opened",
}
STORAGE_ERRNOS: dict[int, str] = {
    errno.ENOSPC: "disk is full",
    errno.EDQUOT: "disk quota exceeded",
    errno.EROFS: "file system is read-only",
    errno.EIO: "disk I/O error",
}


def storage_error_reason(error: BaseException) -> str | None:
    """
    Return a short reason when ``error`` (or an exception it was raised from) is a storage
    failure, else None.
    """
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, OSError) and current.errno in STORAGE_ERRNOS:
            return STORAGE_ERRNOS[current.errno]
        text = str(current).lower()
        for marker, reason in STORAGE_ERROR_MARKERS.items():
            if marker in text:
                return reason
        current = current.__cause__ or current.__context__
    return None


def storage_paths(config: Config) -> list[Path]:
    """Directories the bot writes to: the SQLite database's folder and the user data folder."""
    paths: list[Path] = []
    db_url = config.get("db_url")
    if db_url:
        try:
            url = make_url(db_url)
            if url.get_backend_name() == "sqlite" and url.database and url.database != ":memory:":
                paths.append(Path(url.database).expanduser().resolve().parent)
        except Exception:
            # Don't log the URL itself: it may hold a database password.
            logger.debug("Could not read the database path from db_url.")
    if config.get("user_data_dir"):
        paths.append(Path(config["user_data_dir"]).expanduser().resolve())
    result: list[Path] = []
    for p in paths:
        while not p.exists() and p != p.parent:
            p = p.parent
        if p not in result:
            result.append(p)
    return result


def lowest_free_space(paths: list[Path]) -> tuple[Path, int] | None:
    """(path, free bytes) of the path with the least free space, or None if none can be read."""
    lowest: tuple[Path, int] | None = None
    for p in paths:
        try:
            free = shutil.disk_usage(p).free
        except OSError:
            continue
        if lowest is None or free < lowest[1]:
            lowest = (p, free)
    return lowest


def format_bytes(n: int) -> str:
    if n >= 1024**3:
        return f"{n / 1024**3:.1f} GB"
    return f"{n / 1024**2:.0f} MB"
