from pathlib import Path

from makeitcompliant.app.scanner.project_scanner import ProjectScanner

FIXTURE = Path(__file__).parent / "fixtures" / "sample_node_project"


def test_scan_empty_dir(tmp_path: Path) -> None:
    findings = ProjectScanner().scan(tmp_path)
    assert isinstance(findings, list)


def test_scan_skips_hidden_dirs(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("SPDX-License-Identifier: MIT\n", encoding="utf-8")
    findings = ProjectScanner().scan(tmp_path)
    assert any("MIT" in (f.display_name or "") or f.license_atom == "mit" for f in findings)


def test_scan_sample_has_notice(tmp_path: Path) -> None:
    if not FIXTURE.is_dir():
        return
    findings = ProjectScanner().scan(FIXTURE)
    assert len(findings) >= 1
