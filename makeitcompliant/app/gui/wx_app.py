"""wxPython desktop application entry."""

from __future__ import annotations

import wx

from makeitcompliant.app.core import file_comparison as fc
from makeitcompliant.app.gui import session as app_session
from makeitcompliant.app.gui.components import ConditionsPanel, SimilarityPanel, UploadPanel
from makeitcompliant.app.gui.project_scan_panel import ProjectScanPanel
from makeitcompliant.app.gui.styles import APP_TITLE
from makeitcompliant.app.utils.logging_config import setup_logging


class MainFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, -1, APP_TITLE, size=(720, 640))

        self.upload_panel = UploadPanel(self)
        self.similarity_panel = SimilarityPanel(self)
        self.project_scan_panel = ProjectScanPanel(self)
        self.conditions_panel: ConditionsPanel | None = None

        self.similarity_panel.Hide()
        self.project_scan_panel.Hide()

        self.root_sizer = wx.BoxSizer(wx.VERTICAL)
        self.root_sizer.Add(self.upload_panel, 1, wx.EXPAND)
        self.root_sizer.Add(self.similarity_panel, 1, wx.EXPAND)
        self.root_sizer.Add(self.project_scan_panel, 1, wx.EXPAND)
        self.SetSizer(self.root_sizer)

        menu_bar = wx.MenuBar()
        analyze_menu = wx.Menu()
        analyze_menu.Append(wx.ID_ANY, "Scan Project Folder…", "Full project compliance scan")
        menu_bar.Append(analyze_menu, "&Analyze")

        view_menu = wx.Menu()
        view_menu.Append(wx.ID_ANY, "Upload Licenses", "Upload license files")
        view_menu.Append(wx.ID_ANY, "Compare Two Licenses", "Similarity metrics")
        view_menu.Append(wx.ID_ANY, "License Conditions", "Permissions and obligations")
        view_menu.Append(wx.ID_ANY, "Project Scanner", "Scan repository compliance")
        menu_bar.Append(view_menu, "&View")
        self.SetMenuBar(menu_bar)

        self.Bind(
            wx.EVT_MENU,
            lambda e: self.show_panel("project"),
            analyze_menu.FindItemByPosition(0),
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.show_panel("upload"),
            view_menu.FindItemByPosition(0),
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.show_panel("similarity"),
            view_menu.FindItemByPosition(1),
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.show_panel("conditions"),
            view_menu.FindItemByPosition(2),
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self.show_panel("project"),
            view_menu.FindItemByPosition(3),
        )

    def show_panel(self, name: str) -> None:
        self.upload_panel.Hide()
        self.similarity_panel.Hide()
        self.project_scan_panel.Hide()
        if self.conditions_panel is not None:
            self.conditions_panel.Hide()

        if name == "upload":
            self.upload_panel.Show(True)
        elif name == "project":
            self.project_scan_panel.Show(True)
        elif name == "similarity":
            self.similarity_panel.Destroy()
            self.similarity_panel = SimilarityPanel(self)
            self.root_sizer.Add(self.similarity_panel, 1, wx.EXPAND)
            self.similarity_panel.Show(True)
        elif name == "conditions":
            if len(app_session.session.files) < 2:
                wx.MessageBox(
                    "Upload two license files first.",
                    APP_TITLE,
                    wx.OK | wx.ICON_WARNING,
                )
                self.upload_panel.Show(True)
                self.Layout()
                return
            if self.conditions_panel is not None:
                self.conditions_panel.Destroy()
            self.conditions_panel = ConditionsPanel(self)
            self.root_sizer.Add(self.conditions_panel, 1, wx.EXPAND)
            self.conditions_panel.Show(True)

        self.Layout()

    def get_classified_files(self) -> list[str] | False:
        files = app_session.session.files
        if len(files) < 2:
            return False
        return fc.classify_two_files(files[0].value, files[1].value)


def main() -> None:
    setup_logging()
    app = wx.App()
    frame = MainFrame()
    frame.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    main()
