import json
from pathlib import Path

from makeitcompliant.app.scanner import parsers


def test_parse_package_json(tmp_path: Path) -> None:
    data = {
        "license": "MIT",
        "dependencies": {"lodash": "^4.0.0"},
        "devDependencies": {"jest": "^29.0.0"},
    }
    p = tmp_path / "package.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    proj, deps = parsers.parse_package_json(p)
    assert proj == "mit"
    assert len(deps) == 2


def test_parse_package_lock(tmp_path: Path) -> None:
    data = {
        "packages": {
            "": {"license": "MIT"},
            "node_modules/lodash": {"license": {"type": "MIT"}},
        }
    }
    p = tmp_path / "package-lock.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    result = parsers.parse_package_lock(p)
    assert "lodash" in result


def test_parse_pyproject_string_license(tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nlicense = "MIT"\n', encoding="utf-8")
    assert parsers.parse_pyproject(p) == "mit"


def test_parse_setup_py() -> None:
    p = Path(__file__).parent / "fixtures" / "sample_node_project" / "setup.py"
    if not p.is_file():
        return
    atom = parsers.parse_setup_py(p)
    assert atom is None or isinstance(atom, str)


def test_parse_requirements(tmp_path: Path) -> None:
    p = tmp_path / "requirements.txt"
    p.write_text("requests>=2.0\n# comment\n\nflask\n", encoding="utf-8")
    names = parsers.parse_requirements(p)
    assert "requests" in names
    assert "flask" in names


def test_parse_cargo_toml(tmp_path: Path) -> None:
    p = tmp_path / "Cargo.toml"
    p.write_text('[package]\nname = "demo"\nlicense = "MIT"\n', encoding="utf-8")
    project, deps = parsers.parse_cargo_toml(p)
    assert project == "mit"
    assert isinstance(deps, list)


def test_parse_go_mod(tmp_path: Path) -> None:
    p = tmp_path / "go.mod"
    p.write_text("module example.com/foo\nrequire github.com/pkg/errors v1.0.0\n", encoding="utf-8")
    deps = parsers.parse_go_mod(p)
    assert "github.com/pkg/errors" in deps


def test_parse_pom_xml(tmp_path: Path) -> None:
    xml = """<?xml version="1.0"?>
    <project xmlns="http://maven.apache.org/POM/4.0.0">
    <licenses><license><name>MIT</name></license></licenses>
  <dependencies><dependency><artifactId>core</artifactId></dependency></dependencies>
    </project>"""
    p = tmp_path / "pom.xml"
    p.write_text(xml, encoding="utf-8")
    project, deps = parsers.parse_pom_xml(p)
    assert project == "mit"
    assert "core" in deps


def test_parse_gemfile(tmp_path: Path) -> None:
    p = tmp_path / "Gemfile"
    p.write_text('gem "rails"\n', encoding="utf-8")
    assert parsers.parse_gemfile(p) == ["rails"]


def test_parse_csproj_spdx(tmp_path: Path) -> None:
    p = tmp_path / "App.csproj"
    p.write_text("<Project><!-- SPDX-License-Identifier: MIT --></Project>", encoding="utf-8")
    assert parsers.parse_csproj(p) == "mit"


def test_scan_source_header(tmp_path: Path) -> None:
    p = tmp_path / "main.py"
    p.write_text("# SPDX-License-Identifier: MIT\nprint(1)\n", encoding="utf-8")
    assert parsers.scan_source_header(p) == "mit"


def test_scan_source_header_gpl(tmp_path: Path) -> None:
    p = tmp_path / "main.c"
    p.write_text("/* GPL version 3 */\n", encoding="utf-8")
    assert parsers.scan_source_header(p) == "gpl_3_0"


def test_scan_source_header_os_error(tmp_path: Path) -> None:
    assert parsers.scan_source_header(tmp_path / "missing.py") is None
