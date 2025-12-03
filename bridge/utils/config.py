"""Runtime configuration helpers for the MCP server."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Final, Optional

from dotenv import load_dotenv

# Load .env file from project root (if it exists)
load_dotenv()


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    value = value.strip().lower()
    return value in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, *, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, *, default: bool = False) -> bool:
    return _parse_bool(os.getenv(name), default=default)


def _env_int(name: str, *, default: int) -> int:
    return _parse_int(os.getenv(name), default=default)


ENABLE_WRITES: Final[bool] = _env_bool("MCP_ENABLE_WRITES", default=False)
MAX_WRITES_PER_REQUEST: Final[int] = _env_int("MCP_MAX_WRITES_PER_REQUEST", default=2)
MAX_ITEMS_PER_BATCH: Final[int] = _env_int("MCP_MAX_ITEMS_PER_BATCH", default=256)

_audit_log_env = os.getenv("MCP_AUDIT_LOG", "").strip()
AUDIT_LOG_PATH: Final[Optional[Path]] = (
    Path(_audit_log_env).expanduser() if _audit_log_env else None
)


def _discover_pdflatex() -> Optional[str]:
    """Auto-discover pdflatex in common locations.

    Search order:
    1. System PATH (via shutil.which)
    2. ~/.local/texlive/*/bin/*/pdflatex (user installations)
    3. /usr/local/texlive/*/bin/*/pdflatex (system-wide installations)

    Returns the first found executable path, or None if not found.
    """
    # Try system PATH first
    system_pdflatex = shutil.which("pdflatex")
    if system_pdflatex:
        return system_pdflatex

    # Search in common TeX Live locations
    search_roots = [
        Path.home() / ".local" / "texlive",
        Path("/usr/local/texlive"),
    ]

    for root in search_roots:
        if not root.exists():
            continue

        # Find all pdflatex binaries under this root
        # Pattern: texlive/YEAR/bin/ARCH/pdflatex
        for year_dir in sorted(root.iterdir(), reverse=True):  # newest first
            if not year_dir.is_dir():
                continue
            bin_dir = year_dir / "bin"
            if not bin_dir.exists():
                continue
            for arch_dir in bin_dir.iterdir():
                if not arch_dir.is_dir():
                    continue
                pdflatex = arch_dir / "pdflatex"
                if pdflatex.is_file() and os.access(pdflatex, os.X_OK):
                    return str(pdflatex)

    return None


def get_pdflatex_path() -> Optional[str]:
    """Get the pdflatex executable path.

    Priority:
    1. PDFLATEX_PATH environment variable (explicit override)
    2. Auto-discovery in common locations

    Returns the path as a string, or None if not found.
    """
    # Check explicit override first
    explicit_path = os.getenv("PDFLATEX_PATH", "").strip()
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        # If explicitly set but invalid, return it anyway (will fail with clear error)
        return explicit_path

    # Fall back to auto-discovery
    return _discover_pdflatex()


__all__ = [
    "AUDIT_LOG_PATH",
    "ENABLE_WRITES",
    "MAX_ITEMS_PER_BATCH",
    "MAX_WRITES_PER_REQUEST",
    "get_pdflatex_path",
]
