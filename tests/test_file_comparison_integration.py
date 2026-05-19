"""Integration tests for file_comparison facade (requires generated Prolog KB)."""

from pathlib import Path
from unittest.mock import patch

from makeitcompliant.app.core import file_comparison as fc
from makeitcompliant.app.prolog.facts_loader import write_runtime_facts


def test_classify_two_files_writes_facts(tmp_path: Path, mit_text: str, gpl3_text: str) -> None:
    out = tmp_path / "facts.pl"
    write_runtime_facts("MIT License", "GNU General Public License v3.0", output_path=out)
    with patch("makeitcompliant.app.prolog.engine.get_prolog_runtime_kb_path", return_value=out):
        with patch("makeitcompliant.app.prolog.engine.prolog_path_for_consult", return_value=str(out)):
            names = fc.classify_two_files(mit_text, gpl3_text)
    assert len(names) == 2
    assert "MIT" in names[0] or "mit" in names[0].lower()
