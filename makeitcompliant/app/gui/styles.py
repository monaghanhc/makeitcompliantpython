"""wxPython fonts and colors (Step 5 will expand)."""

from __future__ import annotations

import wx

APP_TITLE = "Make It Compliant"


def header_font() -> wx.Font:
    return wx.Font(wx.FontInfo(15).Bold().Underlined())


def body_font() -> wx.Font:
    return wx.Font(wx.FontInfo(10))
