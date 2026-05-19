def test_package_imports() -> None:
    import makeitcompliant  # noqa: F401
    from makeitcompliant.app.core.compliance_engine import ComplianceEngine  # noqa: F401

    pytest = __import__("pytest")
    wx = pytest.importorskip("wx")
    assert wx is not None
    from makeitcompliant.app.gui import wx_app  # noqa: F401
