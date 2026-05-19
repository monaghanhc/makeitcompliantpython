"""SWI-Prolog availability checks (free, open-source engine)."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("prolog.runtime")


@dataclass(frozen=True)
class PrologStatus:
    available: bool
    executable: str | None
    version_line: str | None
    message: str


def check_prolog() -> PrologStatus:
    exe = shutil.which("swipl")
    if not exe:
        return PrologStatus(
            available=False,
            executable=None,
            version_line=None,
            message=(
                "SWI-Prolog not found. Install free SWI-Prolog from https://www.swi-prolog.org "
                "and add swipl to PATH for full rule-based compliance analysis."
            ),
        )
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        version = (result.stdout or result.stderr or "").strip().split("\n")[0]
        return PrologStatus(
            available=True,
            executable=exe,
            version_line=version,
            message=f"SWI-Prolog ready: {version}",
        )
    except OSError as exc:
        return PrologStatus(
            available=False,
            executable=exe,
            version_line=None,
            message=f"SWI-Prolog found but failed to run: {exc}",
        )


def require_prolog() -> PrologStatus:
    status = check_prolog()
    if not status.available:
        logger.warning(status.message)
    return status
