from pathlib import Path

from makeitcompliant.app.prolog.session_facts import write_project_session


def test_write_project_session(tmp_path: Path) -> None:
    out = write_project_session(
        "mit",
        [("lodash", "mit"), ("weird/name!", "unknown")],
        output_path=tmp_path / "session.pl",
    )
    text = out.read_text(encoding="utf-8")
    assert "project_license(mit)" in text
    assert 'dependency("lodash", mit)' in text
    assert "unknown" in text
