"""wxPython panels for upload, similarity, conditions, and Prolog console."""

from __future__ import annotations

import wx

from makeitcompliant.app.core import file_comparison as fc
from makeitcompliant.app.core.license_models import define
from makeitcompliant.app.core.validation import ValidationError, read_license_file
from makeitcompliant.app.gui import session as app_session
from makeitcompliant.app.gui import theme
from makeitcompliant.app.gui.styles import body_font, header_font, subheader_font
from makeitcompliant.app.gui.util import find_main_frame
from makeitcompliant.app.gui.widgets import (
    CardPanel,
    FieldLabel,
    FileChipList,
    MutedLabel,
    ResultBox,
    SectionHeader,
)
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("gui")


def _describe(atom: str) -> str:
    text = define(atom)
    return text if text else atom


class UploadPanel(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent)
        theme.apply_app_background(self)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            SectionHeader(self, "Import license texts", "Add two files to compare or analyze."),
            0,
            wx.EXPAND,
        )

        card = CardPanel(self)
        card.add(FieldLabel(card, "Selected file"), 0, wx.BOTTOM, theme.PADDING_SM)
        self.file_path = wx.TextCtrl(
            card, style=wx.TE_READONLY | wx.BORDER_NONE, size=(-1, 32),
        )
        self.file_path.SetBackgroundColour(theme.BG_INPUT)
        card.add(self.file_path, 0, wx.EXPAND | wx.BOTTOM, theme.PADDING)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        browse_button = wx.Button(card, label="Browse…")
        import_button = wx.Button(card, label="Import license")
        theme.style_secondary_button(browse_button)
        theme.style_primary_button(import_button)
        browse_button.Bind(wx.EVT_BUTTON, self.on_browse)
        import_button.Bind(wx.EVT_BUTTON, self.on_import)
        btn_row.Add(browse_button, 0, wx.RIGHT, theme.PADDING_SM)
        btn_row.Add(import_button, 0)
        card.add(btn_row, 0, wx.BOTTOM, theme.PADDING)

        card.add(FieldLabel(card, "Imported licenses"), 0, wx.BOTTOM, theme.PADDING_SM)
        self.chips = FileChipList(card)
        card.add(self.chips, 0, wx.EXPAND)
        tip = MutedLabel(card, "Tip: import at least two licenses, then use Compare or Conditions.")
        card.add(tip, 0, wx.TOP, theme.PADDING)

        root.Add(card, 1, wx.EXPAND | wx.ALL, theme.PADDING)
        self.SetSizer(root)
        self._refresh_chips()

    def _refresh_chips(self) -> None:
        names = [f.name for f in app_session.session.files]
        self.chips.set_files(names)

    def on_browse(self, event: wx.CommandEvent) -> None:
        dlg = wx.FileDialog(
            self,
            "Choose a license file",
            wildcard="License files (*.txt;*.md)|*.txt;*.md|All (*.*)|*.*",
            style=wx.FD_OPEN,
        )
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
        self._refresh_chips()
        self.file_path.SetValue("")
        frame = find_main_frame(self)
        if frame is not None and hasattr(frame, "SetStatusText"):
            n = len(app_session.session.files)
            frame.SetStatusText(f"Imported: {uploaded.name} ({n} in session)")


class SimilarityPanel(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent)
        theme.apply_app_background(self)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            SectionHeader(
                self,
                "Compare licenses",
                "Cosine & Jaccard metrics, or full ML + SWI-Prolog analysis.",
            ),
            0,
            wx.EXPAND,
        )

        card = CardPanel(self)
        names = [f.name for f in app_session.session.files]
        files_label = ", ".join(names) if names else "(none yet)"
        card.add(FieldLabel(card, "Files in session"), 0, wx.BOTTOM, theme.PADDING_SM)
        self._files_label = MutedLabel(card, files_label)
        card.add(self._files_label, 0, wx.BOTTOM, theme.PADDING)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        cosine_btn = wx.Button(card, label="Cosine")
        jaccard_btn = wx.Button(card, label="Jaccard")
        analyze_btn = wx.Button(card, label="ML + Prolog analyze")
        for b in (cosine_btn, jaccard_btn):
            theme.style_secondary_button(b)
        theme.style_primary_button(analyze_btn)
        cosine_btn.Bind(wx.EVT_BUTTON, self.on_cosine)
        jaccard_btn.Bind(wx.EVT_BUTTON, self.on_jaccard)
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_full_analyze)
        btn_row.Add(cosine_btn, 0, wx.RIGHT, theme.PADDING_SM)
        btn_row.Add(jaccard_btn, 0, wx.RIGHT, theme.PADDING_SM)
        btn_row.Add(analyze_btn, 0)
        card.add(btn_row, 0, wx.BOTTOM, theme.PADDING)

        card.add(FieldLabel(card, "Results"), 0, wx.BOTTOM, theme.PADDING_SM)
        self.comparison_results = ResultBox(card, min_height=200)
        card.add(self.comparison_results, 1, wx.EXPAND)

        root.Add(card, 1, wx.EXPAND | wx.ALL, theme.PADDING)
        self.SetSizer(root)

    def refresh(self) -> None:
        """Update file list after uploads."""
        names = [f.name for f in app_session.session.files]
        empty = "(none yet — upload licenses first)"
        self._files_label.SetLabel(", ".join(names) if names else empty)

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
        self.comparison_results.SetValue(f"Cosine similarity\n{'─' * 24}\n{score:.2f}%")

    def on_jaccard(self, event: wx.CommandEvent) -> None:
        pair = self._require_two_files()
        if not pair:
            return
        score = fc.jaccard_similarity(pair[0], pair[1]) * 100
        self.comparison_results.SetValue(f"Jaccard similarity\n{'─' * 24}\n{score:.2f}%")

    def on_full_analyze(self, event: wx.CommandEvent) -> None:
        pair = self._require_two_files()
        if not pair:
            return
        from makeitcompliant.app.core.license_analysis import analyze_license_pair

        analysis = analyze_license_pair(pair[0], pair[1])
        lines = [
            "ML + Prolog analysis",
            "─" * 24,
            f"License A: {analysis.license_a.display_name}",
            f"  Confidence: {analysis.license_a.confidence:.0%} "
            f"({analysis.license_a.detection_method})",
            f"License B: {analysis.license_b.display_name}",
            f"  Confidence: {analysis.license_b.confidence:.0%} "
            f"({analysis.license_b.detection_method})",
            "",
            ConditionsPanel._compat_summary(analysis),
        ]
        self.comparison_results.SetValue("\n".join(lines))


class ConditionsPanel(wx.ScrolledWindow):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent, style=wx.VSCROLL)
        theme.apply_app_background(self)
        self.SetScrollRate(0, 12)

        main = find_main_frame(self)
        analysis = main.get_license_pair_analysis() if main else False

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            SectionHeader(
                self,
                "License conditions",
                "Permissions, obligations, and Prolog compatibility.",
            ),
            0,
            wx.EXPAND,
        )

        if analysis is False or main is None:
            err = wx.BoxSizer(wx.VERTICAL)
            err.Add(
                SectionHeader(self, "License conditions", "Upload two licenses to continue."),
                0,
                wx.EXPAND,
            )
            card = CardPanel(self)
            card.add(
                MutedLabel(card, "Import two license files on the Upload page, then return here."),
                0,
                wx.ALL,
                theme.PADDING,
            )
            err.Add(card, 1, wx.EXPAND | wx.ALL, theme.PADDING)
            self.SetSizer(err)
            self.FitInside()
            return

        compat_card = CardPanel(self)
        compat_card.add(
            FieldLabel(compat_card, "Cross-license analysis"), 0, wx.BOTTOM, theme.PADDING_SM,
        )
        compat = wx.StaticText(compat_card, label=self._compat_summary(analysis))
        compat.SetFont(body_font())
        compat.Wrap(800)
        compat_card.add(compat, 0, wx.EXPAND)
        if analysis.obligations:
            compat_card.add_spacer(theme.PADDING_SM)
            obl = wx.StaticText(
                compat_card,
                label="Obligations: " + "; ".join(analysis.obligations[:8]),
            )
            obl.SetFont(body_font())
            obl.SetForegroundColour(theme.TEXT_MUTED)
            obl.Wrap(800)
            compat_card.add(obl, 0, wx.EXPAND)
        root.Add(compat_card, 0, wx.EXPAND | wx.ALL, theme.PADDING)

        row = wx.BoxSizer(wx.HORIZONTAL)
        a, b = analysis.license_a, analysis.license_b
        row.Add(
            self._license_card(self, "License A", a.display_name, a.confidence, a),
            1,
            wx.EXPAND | wx.RIGHT,
            theme.PADDING_SM,
        )
        row.Add(
            self._license_card(self, "License B", b.display_name, b.confidence, b),
            1,
            wx.EXPAND | wx.LEFT,
            theme.PADDING_SM,
        )
        root.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, theme.PADDING)

        console_btn = wx.Button(self, label="Open Prolog console")
        theme.style_primary_button(console_btn)
        console_btn.Bind(wx.EVT_BUTTON, self.on_open_console)
        root.Add(console_btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, theme.PADDING)

        self.SetSizer(root)
        self.FitInside()
        self.Layout()

    def _license_card(self, parent, side: str, name: str, confidence: float, lic) -> CardPanel:
        card = CardPanel(parent)
        card.add(FieldLabel(card, side), 0, wx.BOTTOM, 4)
        title = wx.StaticText(card, label=f"{name}")
        title.SetFont(header_font())
        card.add(title, 0, wx.BOTTOM, 2)
        badge = wx.StaticText(card, label=f"ML confidence: {confidence:.0%}")
        badge.SetForegroundColour(theme.ACCENT)
        badge.SetFont(subheader_font())
        card.add(badge, 0, wx.BOTTOM, theme.PADDING)

        for section, items in (
            ("You can", lic.permissions),
            ("Distribution", lic.distribution_conditions),
            ("Modification", lic.modification_conditions),
            ("Limitations", lic.limitations),
        ):
            if items:
                card.add(FieldLabel(card, section), 0, wx.TOP, theme.PADDING_SM)
                for item in items:
                    line = wx.StaticText(card, label=f"• {_describe(item)}")
                    line.SetFont(body_font())
                    line.Wrap(360)
                    card.add(line, 0, wx.LEFT, 8)
        return card

    @staticmethod
    def _compat_summary(analysis) -> str:
        if not analysis.prolog_available:
            return f"Prolog: {analysis.prolog_message}"
        compat = "Compatible" if analysis.cross_compatible else "Not compatible"
        return (
            f"{compat} · Risk: {analysis.cross_risk or '—'}\n"
            f"{analysis.cross_explanation or ''}"
        )

    def on_open_console(self, event: wx.CommandEvent) -> None:
        PrologConsoleFrame()


class PrologConsoleFrame(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, -1, "Prolog Console", size=(520, 420))
        theme.apply_app_background(self)
        panel = wx.Panel(self)
        theme.apply_app_background(panel)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(
            SectionHeader(panel, "SWI-Prolog console", "Run queries against the knowledge base."),
            0,
            wx.EXPAND,
        )

        card = CardPanel(panel)
        self.console = ResultBox(card, min_height=240)
        card.add(self.console, 1, wx.EXPAND | wx.BOTTOM, theme.PADDING)
        self.query_input = wx.TextCtrl(card, style=wx.TE_PROCESS_ENTER, size=(-1, 36))
        self.query_input.SetHint("e.g. can_use_commercially(X)")
        self.query_input.SetBackgroundColour(theme.BG_INPUT)
        enter = wx.Button(card, label="Run query")
        theme.style_primary_button(enter)
        enter.Bind(wx.EVT_BUTTON, self.on_query)
        self.query_input.Bind(wx.EVT_TEXT_ENTER, self.on_query)
        query_row = wx.BoxSizer(wx.HORIZONTAL)
        query_row.Add(self.query_input, 1, wx.EXPAND | wx.RIGHT, theme.PADDING_SM)
        query_row.Add(enter, 0)
        card.add(query_row, 0, wx.EXPAND)
        box.Add(card, 1, wx.EXPAND | wx.ALL, theme.PADDING)
        panel.SetSizer(box)
        self.Show(True)

    def on_query(self, event: wx.Event) -> None:
        goal = self.query_input.GetValue().strip()
        if not goal or goal == "Enter Prolog query here":
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
