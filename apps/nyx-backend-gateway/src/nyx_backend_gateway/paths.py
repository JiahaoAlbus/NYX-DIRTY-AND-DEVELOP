from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def backend_src() -> Path:
    return repo_root() / "apps" / "nyx-backend" / "src"


def run_root() -> Path:
    return repo_root() / "apps" / "nyx-backend-gateway" / "runs"


def db_path() -> Path:
    return repo_root() / "apps" / "nyx-backend-gateway" / "data" / "nyx_gateway.db"
