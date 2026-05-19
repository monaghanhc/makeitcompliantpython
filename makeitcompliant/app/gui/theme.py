"""Application color palette and wx theme helpers."""

from __future__ import annotations

import wx

# Slate + teal compliance theme
BG_APP = wx.Colour(241, 245, 249)
BG_CARD = wx.Colour(255, 255, 255)
BG_NAV = wx.Colour(15, 23, 42)
BG_NAV_ACTIVE = wx.Colour(30, 41, 59)
BG_HEADER = wx.Colour(15, 118, 110)
BG_INPUT = wx.Colour(248, 250, 252)
FG_NAV = wx.Colour(226, 232, 240)
FG_NAV_DIM = wx.Colour(148, 163, 184)
FG_HEADER = wx.Colour(255, 255, 255)
TEXT_PRIMARY = wx.Colour(15, 23, 42)
TEXT_MUTED = wx.Colour(100, 116, 139)
TEXT_ON_ACCENT = wx.Colour(255, 255, 255)
ACCENT = wx.Colour(15, 118, 110)
ACCENT_DARK = wx.Colour(13, 94, 89)
BORDER = wx.Colour(226, 232, 240)
SUCCESS = wx.Colour(22, 163, 74)
WARNING = wx.Colour(217, 119, 6)
DANGER = wx.Colour(220, 38, 38)

PADDING = 16
PADDING_SM = 8
CONTENT_MAX = 900


def apply_app_background(panel: wx.Window) -> None:
    panel.SetBackgroundColour(BG_APP)


def apply_card(panel: wx.Window) -> None:
    panel.SetBackgroundColour(BG_CARD)


def apply_nav(panel: wx.Window) -> None:
    panel.SetBackgroundColour(BG_NAV)


def style_primary_button(btn: wx.Button) -> None:
    btn.SetBackgroundColour(ACCENT)
    btn.SetForegroundColour(TEXT_ON_ACCENT)
    try:
        btn.SetFont(btn.GetFont().Bold())
    except Exception:
        pass


def style_secondary_button(btn: wx.Button) -> None:
    btn.SetBackgroundColour(BG_CARD)
    btn.SetForegroundColour(TEXT_PRIMARY)


def style_nav_button(btn: wx.Button, *, active: bool = False) -> None:
    if active:
        btn.SetBackgroundColour(BG_NAV_ACTIVE)
        btn.SetForegroundColour(FG_NAV)
    else:
        btn.SetBackgroundColour(BG_NAV)
        btn.SetForegroundColour(FG_NAV_DIM)
    btn.SetFont(btn.GetFont().Bold() if active else btn.GetFont())


def risk_colour(level: str) -> wx.Colour:
    key = (level or "").lower()
    if key in ("critical", "high"):
        return DANGER
    if key in ("medium",):
        return WARNING
    if key in ("low",):
        return SUCCESS
    return TEXT_MUTED
