from makeitcompliant.app.gui.session import AppSession, LicenseFileEntry, session


def test_app_session_add_and_summary() -> None:
    s = AppSession()
    s.add("a", "license a")
    s.add("b", "license b")
    assert s.names_summary() == "a b"
    assert len(s.files) == 2
    assert s.files[0] == LicenseFileEntry("a", "license a")
    s.clear()
    assert s.files == []


def test_module_session_singleton() -> None:
    session.clear()
    session.add("test", "x")
    assert any(f.name == "test" for f in session.files)
    session.clear()
