"""wxPython fonts and application title."""

from __future__ import annotations

import wx

APP_TITLE = "Make It Compliant"
APP_TAGLINE = "ML detection · SWI-Prolog reasoning · Free & open source"


def title_font() -> wx.Font:
    return wx.Font(wx.FontInfo(18).Bold().Family(wx.FONTFAMILY_SWISS))


def header_font() -> wx.Font:
    return wx.Font(wx.FontInfo(14).Bold().Family(wx.FONTFAMILY_SWISS))


def subheader_font() -> wx.Font:
    return wx.Font(wx.FontInfo(11).Bold().Family(wx.FONTFAMILY_SWISS))


def body_font() -> wx.Font:
    return wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_SWISS))


def small_font() -> wx.Font:
    return wx.Font(wx.FontInfo(9).Family(wx.FONTFAMILY_SWISS))
