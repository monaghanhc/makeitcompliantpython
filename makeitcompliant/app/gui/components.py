"""wxPython panels for upload, similarity, conditions, and Prolog console."""

from __future__ import annotations

import wx

from makeitcompliant.app.core import file_comparison as fc
from makeitcompliant.app.core.license_models import define
from makeitcompliant.app.core.validation import ValidationError, read_license_file
from makeitcompliant.app.gui import session as app_session
from makeitcompliant.app.gui.styles import body_font, header_font
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("gui")


def _describe(atom: str) -> str:
    text = define(atom)
    return text if text else atom


def _safe_list(items: list[str] | None) -> list[str]:
    return items if items else []


class UploadPanel(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent)
        self.file_path = wx.TextCtrl(self, size=(400, -1), style=wx.TE_READONLY)
        self.uploaded_files = wx.TextCtrl(self, style=wx.TE_READONLY)
        browse_button = wx.Button(self, -1, "Browse...")
        import_button = wx.Button(self, -1, "Import")

        browse_button.Bind(wx.EVT_BUTTON, self.on_browse)
        import_button.Bind(wx.EVT_BUTTON, self.on_import)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.file_path, 0, 0, 0)
        sizer.Add(browse_button, 0, 0, 0)
        sizer.Add(import_button, 0, 0, 0)
        sizer.Add(self.uploaded_files, 0, wx.EXPAND, 0)
        self.SetSizer(sizer)

    def on_browse(self, event: wx.CommandEvent) -> None:
        dlg = wx.FileDialog(self, "Choose a license file", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_path.SetValue(dlg.GetPath())
        dlg.Destroy()

    def on_import(self, event: wx.CommandEvent) -> None:
        path = self.file_path.GetValue()
        if not path:
            wx.MessageBox("Select a file first.", "Import", wx.OK | wx.ICON_WARNING)
            return
        try:
            uploaded = read_license_file(path)
        except ValidationError as exc:
            wx.MessageBox(str(exc), "Import failed", wx.OK | wx.ICON_ERROR)
            return
        app_session.session.add(uploaded.name, uploaded.value)
        self.uploaded_files.SetValue(app_session.session.names_summary())


class SimilarityPanel(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent)
        self.files_to_compare = wx.TextCtrl(self, size=(400, -1), style=wx.TE_READONLY)
        self.comparison_results = wx.TextCtrl(self, size=(400, -1), style=wx.TE_READONLY)

        names = app_session.session.names_summary()
        self.files_to_compare.SetValue(f"Uploaded files: {names}")

        cosine_btn = wx.Button(self, -1, "Cosine Sim")
        jaccard_btn = wx.Button(self, -1, "Jaccard Sim")
        cosine_btn.Bind(wx.EVT_BUTTON, self.on_cosine)
        jaccard_btn.Bind(wx.EVT_BUTTON, self.on_jaccard)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        btn_row.Add(cosine_btn, 0, 0, 0)
        btn_row.Add(jaccard_btn, 0, 0, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.files_to_compare, 0, 0, 0)
        sizer.Add(btn_row, 0, 0, 0)
        sizer.Add(self.comparison_results, 0, 0, 0)
        self.SetSizer(sizer)

    def _require_two_files(self) -> tuple[str, str] | None:
        files = app_session.session.files
        if len(files) < 2:
            wx.MessageBox(
                "Upload at least two license files on the Upload page.",
                "Similarity",
                wx.OK | wx.ICON_WARNING,
            )
            return None
        return files[0].value, files[1].value

    def on_cosine(self, event: wx.CommandEvent) -> None:
        pair = self._require_two_files()
        if not pair:
            return
        score = fc.cosine_similarity(pair[0], pair[1]) * 100
        self.comparison_results.SetValue(f"Cosine Similarity: {score:.2f} %")

    def on_jaccard(self, event: wx.CommandEvent) -> None:
        pair = self._require_two_files()
        if not pair:
            return
        score = fc.jaccard_similarity(pair[0], pair[1]) * 100
        self.comparison_results.SetValue(f"Jaccard Similarity: {score:.2f} %")


class ConditionsPanel(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent)
        header = header_font()
        body = body_font()

        frame = self.GetParent()
        assert hasattr(frame, "get_classified_files")
        files = frame.get_classified_files()  # type: ignore[attr-defined]

        if files is False:
            wx.MessageBox(
                "Upload two license files before opening the Conditions page.",
                "Conditions",
                wx.OK | wx.ICON_WARNING,
            )
            self.SetSizer(wx.BoxSizer())
            return

        permissions = fc.get_permissions()
        d_conditions = fc.get_conditions_for_distribution()
        m_conditions = fc.get_conditions_for_modification()
        limitations = fc.get_limitations()

        file_a_box = self._license_column(
            self,
            files[0],
            _safe_list(permissions[0]),
            _safe_list(d_conditions[0]),
            _safe_list(m_conditions[0]),
            _safe_list(limitations[0]),
            header,
            body,
        )
        file_b_box = self._license_column(
            self,
            files[1],
            _safe_list(permissions[1]),
            _safe_list(d_conditions[1]),
            _safe_list(m_conditions[1]),
            _safe_list(limitations[1]),
            header,
            body,
        )

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(file_a_box, 0, flag=wx.LEFT | wx.RIGHT, border=20)
        row.Add(file_b_box, 0, flag=wx.LEFT | wx.RIGHT, border=20)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(row)
        console_btn = wx.Button(self, label="Prolog Console")
        console_btn.Bind(wx.EVT_BUTTON, self.on_open_console)
        root.Add(console_btn, flag=wx.CENTER)
        self.SetSizer(root)
        self.Layout()

    @staticmethod
    def _license_column(
        panel: wx.Panel,
        license_name: str,
        permissions: list[str],
        dist_conditions: list[str],
        mod_conditions: list[str],
        limitations: list[str],
        header: wx.Font,
        body: wx.Font,
    ) -> wx.BoxSizer:
        col = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, -1, f"With The {license_name} You Can", style=wx.ALIGN_CENTER)
        title.SetFont(header)
        title.Wrap(260)
        col.Add(title, 0)

        for perm in permissions:
            line = wx.StaticText(panel, -1, f"-{_describe(perm)}")
            line.SetFont(body)
            line.Wrap(260)
            col.Add(line)

        col.Add(wx.BoxSizer(), 0, flag=wx.TOP | wx.BOTTOM, border=20)

        if dist_conditions:
            h = wx.StaticText(panel, -1, "Conditions For Distribution", style=wx.ALIGN_CENTER)
            h.SetFont(header)
            h.Wrap(260)
            col.Add(h)
            for item in dist_conditions:
                line = wx.StaticText(panel, -1, f"-{_describe(item)}")
                line.SetFont(body)
                line.Wrap(260)
                col.Add(line)
            col.Add(wx.BoxSizer(), 0, flag=wx.TOP | wx.BOTTOM, border=20)

        if mod_conditions:
            h = wx.StaticText(panel, -1, "Conditions For Modification", style=wx.ALIGN_CENTER)
            h.SetFont(header)
            h.Wrap(260)
            col.Add(h)
            for item in mod_conditions:
                line = wx.StaticText(panel, -1, f"-{_describe(item)}")
                line.SetFont(body)
                line.Wrap(260)
                col.Add(line)
            col.Add(wx.BoxSizer(), 0, flag=wx.TOP | wx.BOTTOM, border=20)

        if limitations:
            h = wx.StaticText(panel, -1, "Limitations", style=wx.ALIGN_CENTER)
            h.SetFont(header)
            h.Wrap(260)
            col.Add(h)
            for item in limitations:
                line = wx.StaticText(panel, -1, f"-{_describe(item)}")
                line.SetFont(body)
                line.Wrap(260)
                col.Add(line)

        return col

    def on_open_console(self, event: wx.CommandEvent) -> None:
        PrologConsoleFrame()


class PrologConsoleFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, -1, "Prolog Console", size=(400, 350))
        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)
        self.console = wx.TextCtrl(
            panel, style=wx.TE_READONLY | wx.TE_MULTILINE, size=(400, 300)
        )
        self.query_input = wx.TextCtrl(
            panel,
            style=wx.TE_PROCESS_ENTER,
            value="Enter Prolog query here",
            size=(400, 50),
        )
        enter = wx.Button(panel, label="Enter")
        enter.Bind(wx.EVT_BUTTON, self.on_query)
        self.query_input.Bind(wx.EVT_TEXT_ENTER, self.on_query)

        query_row = wx.BoxSizer(wx.HORIZONTAL)
        query_row.Add(self.query_input, proportion=1)
        query_row.Add(enter)
        box.Add(self.console, 1, wx.EXPAND)
        box.Add(query_row)
        panel.SetSizer(box)
        self.Show(True)

    def on_query(self, event: wx.CommandEvent) -> None:
        goal = self.query_input.GetValue().strip()
        if not goal:
            return
        logger.info("Prolog query: %s", goal)
        try:
            result = fc.query(goal)
        except Exception as exc:
            self.console.AppendText(f"Error: {exc}\n\n")
            return
        if result is False:
            self.console.AppendText("false.\n\n")
            return
        for binding in result:
            parts = [f"{k}: {v}" for k, v in binding.items()]
            self.console.AppendText("; ".join(parts) + ".\n")
        self.console.AppendText("\n")
