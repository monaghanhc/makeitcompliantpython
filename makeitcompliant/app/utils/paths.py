"""Cross-platform resource paths (source tree and PyInstaller bundle)."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path


def _frozen_base() -> Path | None:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return None


@lru_cache(maxsize=1)
def get_resource_root() -> Path:
    """Directory containing license_templates/, Prolog KB, and web/."""
    frozen = _frozen_base()
    if frozen is not None:
        return frozen

    # makeitcompliant/app/utils/paths.py -> repo root is parents[3]
    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    if (repo_root / "license_templates").is_dir():
        return repo_root

    # Fallback: current working directory (legacy launches)
    cwd = Path.cwd()
    if (cwd / "license_templates").is_dir():
        return cwd

    return repo_root


def get_license_templates_dir() -> Path:
    return get_resource_root() / "license_templates"


def get_prolog_base_kb_path() -> Path:
    return get_resource_root() / "allLicenseFactsBaseCopy.pl"


def get_prolog_runtime_kb_path() -> Path:
    """Writable generated KB; prefer cwd when running from source."""
    if not getattr(sys, "frozen", False):
        cwd_candidate = Path.cwd() / "allLicenseFacts.pl"
        if cwd_candidate.parent.exists():
            return cwd_candidate
    return get_resource_root() / "allLicenseFacts.pl"


def get_web_dir() -> Path:
    return get_resource_root() / "web"


def get_prolog_compliance_kb_dir() -> Path:
    return get_resource_root() / "prolog" / "kb" / "compliance"


def get_prolog_session_facts_path() -> Path:
    if not getattr(sys, "frozen", False):
        cwd_candidate = Path.cwd() / "compliance_session.pl"
        if cwd_candidate.parent.exists():
            return cwd_candidate
    return get_resource_root() / "compliance_session.pl"


COMPLIANCE_KB_FILES: tuple[str, ...] = (
    "licenses.pl",
    "families.pl",
    "obligations.pl",
    "requirements.pl",
    "compatibility.pl",
    "analysis.pl",
    "queries.pl",
)


def prolog_path_for_consult(path: Path) -> str:
    """Path string safe for Prolog consult/1 on Windows."""
    return path.resolve().as_posix()
