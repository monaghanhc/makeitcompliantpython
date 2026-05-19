"""Generate runtime Prolog KB with license_a / license_b facts."""

from __future__ import annotations

from pathlib import Path

from makeitcompliant.app.utils.logging_config import get_logger
from makeitcompliant.app.utils.paths import get_prolog_base_kb_path, get_prolog_runtime_kb_path

logger = get_logger("prolog.facts_loader")


def _escape_prolog_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def read_base_kb(path: Path | None = None) -> str:
    kb_path = path or get_prolog_base_kb_path()
    if not kb_path.is_file():
        raise FileNotFoundError(f"Prolog base knowledge base not found: {kb_path}")
    return kb_path.read_text(encoding="utf-8")


def write_runtime_facts(
    license_a: str | None = None,
    license_b: str | None = None,
    *,
    base_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """
    Write allLicenseFacts.pl = base KB + optional license_a/license_b facts.

    Fixes legacy bug that duplicated the entire base file when adding license_b.
    """
    base = read_base_kb(base_path)
    out = output_path or get_prolog_runtime_kb_path()
    lines: list[str] = [base.rstrip(), ""]
    if license_a:
        lines.append(f'license_a("{_escape_prolog_string(license_a)}").')
    if license_b:
        lines.append(f'license_b("{_escape_prolog_string(license_b)}").')
    lines.append("")
    content = "\n".join(lines)
    out.write_text(content, encoding="utf-8")
    logger.debug("Wrote runtime Prolog KB to %s", out)
    return out
