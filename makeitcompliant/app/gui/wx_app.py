"""wxPython desktop application entry."""

from __future__ import annotations

import wx

from makeitcompliant.app.gui import session as app_session
from makeitcompliant.app.gui import theme
from makeitcompliant.app.gui.components import ConditionsPanel, SimilarityPanel, UploadPanel
from makeitcompliant.app.gui.project_scan_panel import ProjectScanPanel
from makeitcompliant.app.gui.styles import APP_TAGLINE, APP_TITLE, body_font, title_font
from makeitcompliant.app.prolog.runtime import check_prolog
from makeitcompliant.app.utils.logging_config import setup_logging

NAV_ITEMS = (
    ("upload", "Upload licenses"),
    ("similarity", "Compare"),
    ("conditions", "Conditions"),
    ("project", "Project scan"),
)


class MainFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, -1, APP_TITLE, size=(1080, 760))
        self.SetMinSize((920, 640))
        theme.apply_app_background(self)
        self.CreateStatusBar()

        self.conditions_panel: ConditionsPanel | None = None
        self._nav_buttons: dict[str, wx.Button] = {}
        self._active = "upload"

        self._build_chrome()
        self.upload_panel = UploadPanel(self._content_area)
        self.similarity_panel = SimilarityPanel(self._content_area)
        self.project_scan_panel = ProjectScanPanel(self._content_area)
        self._build_panels()
        self._build_menu()
        self.show_panel("upload")

    def _build_chrome(self) -> None:
        root = wx.BoxSizer(wx.HORIZONTAL)

        nav = wx.Panel(self)
        theme.apply_nav(nav)
        nav.SetMinSize((232, -1))
        nav_sizer = wx.BoxSizer(wx.VERTICAL)

        brand = wx.StaticText(nav, label=APP_TITLE)
        brand.SetFont(title_font())
        brand.SetForegroundColour(theme.FG_NAV)
        tag = wx.StaticText(nav, label=APP_TAGLINE)
        tag.SetFont(body_font())
        tag.SetForegroundColour(theme.FG_NAV_DIM)
        tag.Wrap(200)

        nav_sizer.Add(brand, 0, wx.ALL, theme.PADDING)
        nav_sizer.Add(tag, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, theme.PADDING)
        nav_sizer.Add(wx.StaticLine(nav), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, theme.PADDING_SM)

        for key, label in NAV_ITEMS:
            btn = wx.Button(nav, label=f"  {label}", size=(208, 44), style=wx.BORDER_NONE)
            btn.Bind(wx.EVT_BUTTON, lambda e, k=key: self.show_panel(k))
            self._nav_buttons[key] = btn
            nav_sizer.Add(btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)

        nav_sizer.AddStretchSpacer()
        nav.SetSizer(nav_sizer)

        content_wrap = wx.Panel(self)
        theme.apply_app_background(content_wrap)
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        self._content_area = wx.Panel(content_wrap)
        theme.apply_app_background(self._content_area)
        content_sizer.Add(self._content_area, 1, wx.EXPAND | wx.ALL, theme.PADDING)
        content_wrap.SetSizer(content_sizer)

        root.Add(nav, 0, wx.EXPAND)
        root.Add(content_wrap, 1, wx.EXPAND)
        self.SetSizer(root)

    def _build_panels(self) -> None:
        self._panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self._content_area.SetSizer(self._panel_sizer)
        for panel in (self.upload_panel, self.similarity_panel, self.project_scan_panel):
            self._panel_sizer.Add(panel, 1, wx.EXPAND)

    def _build_menu(self) -> None:
        menu_bar = wx.MenuBar()
        analyze_menu = wx.Menu()
        analyze_menu.Append(wx.ID_ANY, "Scan Project Folder…")
        menu_bar.Append(analyze_menu, "&Analyze")
        view_menu = wx.Menu()
        for _, label in NAV_ITEMS:
            view_menu.Append(wx.ID_ANY, label)
        menu_bar.Append(view_menu, "&View")
        self.SetMenuBar(menu_bar)

        self.Bind(
            wx.EVT_MENU,
            lambda e: self.show_panel("project"),
            id=analyze_menu.FindItemByPosition(0).GetId(),
        )
        for i, (key, _) in enumerate(NAV_ITEMS):
            self.Bind(
                wx.EVT_MENU,
                lambda e, k=key: self.show_panel(k),
                id=view_menu.FindItemByPosition(i).GetId(),
            )

    def _set_nav_active(self, name: str) -> None:
        self._active = name
        for key, btn in self._nav_buttons.items():
            theme.style_nav_button(btn, active=(key == name))

    def _hide_all_panels(self) -> None:
        self.upload_panel.Hide()
        self.similarity_panel.Hide()
        self.project_scan_panel.Hide()
        if self.conditions_panel is not None:
            self.conditions_panel.Hide()

    def _destroy_conditions_panel(self) -> None:
        if self.conditions_panel is None:
            return
        self._panel_sizer.Detach(self.conditions_panel)
        self.conditions_panel.Destroy()
        self.conditions_panel = None

    def show_panel(self, name: str) -> None:
        if name == "conditions" and len(app_session.session.files) < 2:
            wx.MessageBox(
                "Upload two license files first (Upload licenses).",
                APP_TITLE,
                wx.OK | wx.ICON_WARNING,
            )
            name = "upload"

        self._hide_all_panels()

        if name == "upload":
            self.upload_panel.Show(True)
            self.SetStatusText("Import license text files to begin.")
        elif name == "project":
            self.project_scan_panel.Show(True)
            self.SetStatusText("Select a project folder and run compliance analysis.")
        elif name == "similarity":
            self.similarity_panel.refresh()
            self.similarity_panel.Show(True)
            self.SetStatusText("Compare metrics or run ML + Prolog analysis.")
        elif name == "conditions":
            self._destroy_conditions_panel()
            self.conditions_panel = ConditionsPanel(self._content_area)
            self._panel_sizer.Add(self.conditions_panel, 1, wx.EXPAND)
            self.conditions_panel.Show(True)
            self.SetStatusText("License permissions and cross-license compatibility.")

        self._set_nav_active(name)
        self.Layout()

    def get_license_pair_analysis(self):
        from makeitcompliant.app.core.license_analysis import analyze_license_pair

        files = app_session.session.files
        if len(files) < 2:
            return False
        return analyze_license_pair(files[0].value, files[1].value)


def main() -> None:
    setup_logging()
    app = wx.App()
    status = check_prolog()
    frame = MainFrame()
    frame.Show(True)
    if status.available:
        frame.SetStatusText(status.version_line or "SWI-Prolog ready")
    else:
        frame.SetStatusText("SWI-Prolog not found — ML detection still works")
        wx.MessageBox(
            status.message + "\n\nML license detection will still work.",
            APP_TITLE,
            wx.OK | wx.ICON_INFORMATION,
        )
    app.MainLoop()


if __name__ == "__main__":
    main()
