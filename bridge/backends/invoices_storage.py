"""Filesystem helpers for the invoice workflow."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator, Optional

import portalocker

from .invoices_models import Invoice


INVOICE_ROOT_NAME = ".mad_invoice"
INVOICES_DIRNAME = "invoices"
INDEX_FILENAME = "index.json"


def get_invoice_root(base_path: Optional[Path] = None) -> Path:
    """
    Resolve the invoice storage root.

    Priority:
    1) MAD_INVOICE_ROOT env var (absolute or relative to cwd)
    2) explicit base_path (caller-provided)
    3) repository root (parent of bridge/) to avoid dropping data in random cwd
    """

    env_root = os.getenv("MAD_INVOICE_ROOT", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()

    if base_path is not None:
        return (base_path / INVOICE_ROOT_NAME).resolve()

    repo_root = Path(__file__).resolve().parents[2]
    return (repo_root / INVOICE_ROOT_NAME).resolve()


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_structure(root: Optional[Path] = None) -> None:
    """Create required directories if they do not exist."""

    invoice_root = get_invoice_root(root)
    _ensure_directory(invoice_root)
    _ensure_directory(invoice_root / INVOICES_DIRNAME)


def _invoice_path(invoice_id: str, root: Optional[Path]) -> Path:
    return get_invoice_root(root) / INVOICES_DIRNAME / f"{invoice_id}.json"


def _index_path(root: Optional[Path]) -> Path:
    return get_invoice_root(root) / INDEX_FILENAME


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict) -> None:
    _ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _json_ready(invoice: Invoice) -> dict:
    return invoice.model_dump(mode="json")


def iter_invoice_paths(root: Optional[Path] = None) -> Iterator[Path]:
    invoices_dir = get_invoice_root(root) / INVOICES_DIRNAME
    if not invoices_dir.exists():
        return iter(())

    paths = [p for p in invoices_dir.iterdir() if p.is_file() and p.suffix == ".json"]
    paths.sort()
    return iter(paths)


def load_invoice(invoice_id: str, root: Optional[Path] = None) -> Invoice:
    path = _invoice_path(invoice_id, root)
    payload = _read_json(path)
    return Invoice.model_validate(payload)


def load_invoice_by_path(path: Path) -> Invoice:
    payload = _read_json(path)
    return Invoice.model_validate(payload)


def save_invoice(invoice: Invoice, root: Optional[Path] = None) -> None:
    path = _invoice_path(invoice.id, root)
    _write_json(path, _json_ready(invoice))


def build_index(root: Optional[Path] = None) -> dict[str, object]:
    ensure_structure(root)
    entries: list[dict[str, object]] = []

    for path in iter_invoice_paths(root):
        invoice = load_invoice_by_path(path)
        entries.append(invoice.to_index_entry())

    entries.sort(key=lambda entry: entry["id"])
    return {"count": len(entries), "invoices": entries}


def save_index(index: dict[str, object], root: Optional[Path] = None) -> None:
    _write_json(_index_path(root), index)


def with_index_lock(root: Optional[Path] = None):
    """Context manager to lock index rebuilds."""

    class _IndexLock:
        def __init__(self, base: Optional[Path]):
            self.base = base
            self._handle = None

        def __enter__(self):
            ensure_structure(self.base)
            lock_file = get_invoice_root(self.base) / ".index.lock"
            lock_file.touch(exist_ok=True)
            self._handle = portalocker.Lock(lock_file, mode="a", timeout=5, flags=portalocker.LOCK_EX)
            self._handle.acquire()
            return lock_file

        def __exit__(self, exc_type, exc, tb):
            if self._handle:
                self._handle.release()

    return _IndexLock(root)


__all__ = [
    "build_index",
    "ensure_structure",
    "get_invoice_root",
    "iter_invoice_paths",
    "load_invoice",
    "load_invoice_by_path",
    "save_index",
    "save_invoice",
    "with_index_lock",
]
