"""Generate dynamic Prolog facts for a project compliance session."""

from __future__ import annotations

import re
from pathlib import Path

from makeitcompliant.app.utils.logging_config import get_logger
from makeitcompliant.app.utils.paths import get_prolog_session_facts_path

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_]")

logger = get_logger("prolog.session_facts")

def _escape_prolog_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _safe_dependency_name(name: str) -> str:
    cleaned = _SAFE_NAME.sub("_", name)[:80]
    return cleaned if cleaned else "dep"


def write_project_session(
    project_license_atom: str,
    dependencies: list[tuple[str, str]],
    *,
    output_path: Path | None = None,
) -> Path:
    """
    Write session facts:
      project_license(mit).
      dependency('requests', apache_2_0).
    """
    out = output_path or get_prolog_session_facts_path()
    lines = [
        "%% Auto-generated project compliance session — do not edit",
        f"project_license({project_license_atom}).",
        "",
    ]
    for dep_name, dep_atom in dependencies:
        quoted = _escape_prolog_string(dep_name)
        lines.append(f'dependency("{quoted}", {dep_atom}).')
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    logger.debug("Wrote Prolog session to %s", out)
    return out
