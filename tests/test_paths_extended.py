import sys
from pathlib import Path

import pytest

from makeitcompliant.app.utils import paths


def test_frozen_resource_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    (tmp_path / "license_templates").mkdir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    paths.get_resource_root.cache_clear()
    root = paths.get_resource_root()
    assert root == tmp_path
    paths.get_resource_root.cache_clear()
    monkeypatch.delattr(sys, "frozen", raising=False)


def test_prolog_path_helpers() -> None:
    p = paths.prolog_path_for_consult(Path("C:/test/file.pl"))
    assert "/" in p
    assert paths.get_web_dir().name == "web"
    assert "licenses.pl" in paths.COMPLIANCE_KB_FILES
