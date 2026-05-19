from makeitcompliant.app.gui.util import find_main_frame


class _Frame:
    def get_license_pair_analysis(self):
        return "ok"

    def GetParent(self):
        return None


class _Panel:
    def __init__(self, parent):
        self._parent = parent

    def GetParent(self):
        return self._parent


def test_find_main_frame_walks_parents() -> None:
    main = _Frame()
    mid = _Panel(main)
    leaf = _Panel(mid)
    assert find_main_frame(leaf) is main


def test_find_main_frame_returns_none() -> None:
    class _Orphan:
        def GetParent(self):
            return None

    assert find_main_frame(_Orphan()) is None
