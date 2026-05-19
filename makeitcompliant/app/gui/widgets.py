"""Reusable styled wx widgets."""

from __future__ import annotations

import wx

from makeitcompliant.app.gui import theme
from makeitcompliant.app.gui.styles import body_font, subheader_font, title_font


class SectionHeader(wx.Panel):
    """Colored strip with title and optional subtitle."""

    def __init__(
        self,
        parent: wx.Window,
        title: str,
        subtitle: str = "",
    ) -> None:
        super().__init__(parent)
        self.SetBackgroundColour(theme.BG_HEADER)
        self.SetMinSize((-1, 72 if subtitle else 56))

        title_ctrl = wx.StaticText(self, label=title)
        title_ctrl.SetFont(title_font())
        title_ctrl.SetForegroundColour(theme.FG_HEADER)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(title_ctrl, 0, wx.LEFT | wx.TOP | wx.RIGHT, theme.PADDING)
        if subtitle:
            sub = wx.StaticText(self, label=subtitle)
            sub.SetFont(body_font())
            sub.SetForegroundColour(theme.FG_HEADER)
            sub.Wrap(700)
            root.Add(sub, 0, wx.ALL, theme.PADDING_SM)
        self.SetSizer(root)


class CardPanel(wx.Panel):
    """White card with padding for form content."""

    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent)
        theme.apply_card(self)
        self._inner = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._inner)

    def add(self, window: wx.Window, proportion: int = 0, flag: int = 0, border: int = 0) -> None:
        self._inner.Add(window, proportion, flag, border)

    def add_spacer(self, pixels: int) -> None:
        self._inner.AddSpacer(pixels)

    def add_stretch(self) -> None:
        self._inner.AddStretchSpacer()


class MutedLabel(wx.StaticText):
    def __init__(self, parent: wx.Window, label: str) -> None:
        super().__init__(parent, label=label)
        self.SetFont(body_font())
        self.SetForegroundColour(theme.TEXT_MUTED)


class FieldLabel(wx.StaticText):
    def __init__(self, parent: wx.Window, label: str) -> None:
        super().__init__(parent, label=label)
        self.SetFont(subheader_font())
        self.SetForegroundColour(theme.TEXT_PRIMARY)


class ResultBox(wx.TextCtrl):
    """Read-only multiline result area."""

    def __init__(self, parent: wx.Window, *, min_height: int = 120) -> None:
        super().__init__(
            parent,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE,
        )
        self.SetMinSize((-1, min_height))
        self.SetBackgroundColour(theme.BG_INPUT)
        self.SetForegroundColour(theme.TEXT_PRIMARY)
        self.SetFont(body_font())


class FileChipList(wx.Panel):
    """Shows uploaded license file names as chips."""

    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent)
        theme.apply_card(self)
        self._sizer = wx.WrapSizer(wx.HORIZONTAL, wx.WRAPSIZER_DEFAULT_FLAGS)
        self._empty = MutedLabel(self, "No licenses imported yet.")
        self._sizer.Add(self._empty, 0, wx.ALL, theme.PADDING_SM)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self._sizer, 0, wx.EXPAND | wx.ALL, theme.PADDING_SM)
        self.SetSizer(outer)

    def set_files(self, names: list[str]) -> None:
        self._sizer.Clear(True)
        if not names:
            self._empty = MutedLabel(self, "No licenses imported yet.")
            self._sizer.Add(self._empty, 0, wx.ALL, theme.PADDING_SM)
        else:
            for name in names:
                chip = wx.StaticText(self, label=f"  {name}  ")
                chip.SetBackgroundColour(theme.BG_INPUT)
                chip.SetForegroundColour(theme.ACCENT_DARK)
                chip.SetFont(body_font().Bold())
                self._sizer.Add(chip, 0, wx.ALL, 4)
        self.Layout()
