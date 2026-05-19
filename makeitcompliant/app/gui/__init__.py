__all__ = ["main"]


def main() -> None:
    from makeitcompliant.app.gui.wx_app import main as run_desktop

    run_desktop()
