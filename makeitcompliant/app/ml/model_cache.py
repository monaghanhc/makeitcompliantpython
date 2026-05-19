"""Cache license templates and ML objects for fast repeated inference."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from makeitcompliant.app.utils.logging_config import get_logger
from makeitcompliant.app.utils.paths import get_license_templates_dir

logger = get_logger("ml.model_cache")


@dataclass(frozen=True)
class TemplateEntry:
    path: Path
    filename: str
    text: str
    prolog_atom: str


@lru_cache(maxsize=1)
def load_template_cache(templates_dir: str | None = None) -> tuple[TemplateEntry, ...]:
    root = Path(templates_dir) if templates_dir else get_license_templates_dir()
    from makeitcompliant.app.core.license_models import normalize_template_name_to_prolog

    entries: list[TemplateEntry] = []
    if not root.is_dir():
        logger.warning("Templates directory missing: %s", root)
        return tuple()

    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Skip template %s: %s", path, exc)
            continue
        entries.append(
            TemplateEntry(
                path=path,
                filename=path.name,
                text=text,
                prolog_atom=normalize_template_name_to_prolog(path.name),
            )
        )
    logger.info("Cached %d license templates", len(entries))
    return tuple(entries)


def clear_template_cache() -> None:
    load_template_cache.cache_clear()
