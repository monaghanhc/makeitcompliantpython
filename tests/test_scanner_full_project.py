import json
from pathlib import Path

from makeitcompliant.app.scanner.models import FindingKind
from makeitcompliant.app.scanner.project_scanner import ProjectScanner


def _write_mini_project(root: Path) -> None:
    (root / "LICENSE").write_text("SPDX-License-Identifier: MIT\n", encoding="utf-8")
    (root / "README.md").write_text("# App\n\nSPDX-License-Identifier: MIT\n", encoding="utf-8")
    (root / "NOTICE").write_text("Third party notices\n", encoding="utf-8")
    (root / "package.json").write_text(
        json.dumps({"license": "MIT", "dependencies": {"left-pad": "1.0.0"}}),
        encoding="utf-8",
    )
    (root / "package-lock.json").write_text(
        json.dumps({"packages": {"node_modules/left-pad": {"license": "MIT"}}}),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text('[project]\nlicense = "MIT"\n', encoding="utf-8")
    (root / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")
    (root / "Cargo.toml").write_text('[package]\nlicense = "MIT"\n', encoding="utf-8")
    (root / "go.mod").write_text("module example.com/app\nrequire rsc.io/quote v1.5.2\n", encoding="utf-8")
    (root / "pom.xml").write_text(
        '<?xml version="1.0"?><project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<licenses><license><name>MIT</name></license></licenses>"
        "<dependencies><dependency><artifactId>core</artifactId></dependency></dependencies>"
        "</project>",
        encoding="utf-8",
    )
    (root / "Gemfile").write_text('gem "rails"\n', encoding="utf-8")
    src = root / "src"
    src.mkdir()
    (src / "main.py").write_text("# SPDX-License-Identifier: MIT\n", encoding="utf-8")
    deep = root / "a" / "b" / "c" / "d" / "e" / "f" / "g" / "h" / "i" / "j" / "k" / "l"
    deep.mkdir(parents=True)
    (deep / "deep.txt").write_text("deep", encoding="utf-8")


def test_scan_comprehensive_project(tmp_path: Path) -> None:
    _write_mini_project(tmp_path)
    findings = ProjectScanner().scan(tmp_path)
    assert findings
    assert any(f.kind == FindingKind.PROJECT_LICENSE for f in findings)
    assert any(f.package_name for f in findings)


def test_scan_not_a_directory(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    import pytest

    with pytest.raises(FileNotFoundError):
        ProjectScanner().scan(f)
