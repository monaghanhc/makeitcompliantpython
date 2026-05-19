"""Project compliance scanner UI with tabbed report and export."""

from __future__ import annotations

import threading
from pathlib import Path

import wx

from makeitcompliant.app.core.compliance_models import ComplianceReport
from makeitcompliant.app.core.project_compliance import ProjectComplianceService
from makeitcompliant.app.core.report_builder import export_json, export_markdown
from makeitcompliant.app.gui import theme
from makeitcompliant.app.gui.styles import APP_TITLE, header_font
from makeitcompliant.app.gui.widgets import (
    CardPanel,
    FieldLabel,
    MutedLabel,
    ResultBox,
    SectionHeader,
)


class ProjectScanPanel(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent)
        theme.apply_app_background(self)
        self._service = ProjectComplianceService()
        self._project_path: Path | None = None
        self._report: ComplianceReport | None = None

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            SectionHeader(
                self,
                "Project compliance scanner",
                "Scan manifests and license files — ML detection + SWI-Prolog risk reasoning.",
            ),
            0,
            wx.EXPAND,
        )

        card = CardPanel(self)
        card.add(FieldLabel(card, "Project folder"), 0, wx.BOTTOM, theme.PADDING_SM)
        self.path_ctrl = wx.TextCtrl(card, style=wx.TE_READONLY | wx.BORDER_NONE)
        self.path_ctrl.SetBackgroundColour(theme.BG_INPUT)
        self.path_ctrl.SetMinSize((-1, 32))
        card.add(self.path_ctrl, 0, wx.EXPAND | wx.BOTTOM, theme.PADDING)

        browse = wx.Button(card, label="Select folder…")
        theme.style_secondary_button(browse)
        browse.Bind(wx.EVT_BUTTON, self._on_browse)
        card.add(browse, 0, wx.BOTTOM, theme.PADDING)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.scan_btn = wx.Button(card, label="Analyze compliance")
        theme.style_primary_button(self.scan_btn)
        self.scan_btn.Bind(wx.EVT_BUTTON, self._on_scan)
        self.export_json_btn = wx.Button(card, label="Export JSON")
        self.export_md_btn = wx.Button(card, label="Export Markdown")
        for b in (self.export_json_btn, self.export_md_btn):
            theme.style_secondary_button(b)
        self.export_json_btn.Bind(wx.EVT_BUTTON, self._on_export_json)
        self.export_md_btn.Bind(wx.EVT_BUTTON, self._on_export_md)
        self.export_json_btn.Disable()
        self.export_md_btn.Disable()
        btn_row.Add(self.scan_btn, 0, wx.RIGHT, theme.PADDING_SM)
        btn_row.Add(self.export_json_btn, 0, wx.RIGHT, theme.PADDING_SM)
        btn_row.Add(self.export_md_btn, 0)
        card.add(btn_row, 0, wx.BOTTOM, theme.PADDING)

        status_row = wx.BoxSizer(wx.HORIZONTAL)
        self.status = MutedLabel(card, "Ready to scan.")
        self.risk_badge = wx.StaticText(card, label="Overall risk: —")
        self.risk_badge.SetFont(header_font())
        self.risk_badge.SetForegroundColour(theme.TEXT_MUTED)
        status_row.Add(self.status, 1, wx.ALIGN_CENTER_VERTICAL)
        status_row.Add(self.risk_badge, 0, wx.ALIGN_CENTER_VERTICAL)
        card.add(status_row, 0, wx.EXPAND)

        root.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, theme.PADDING)

        self.notebook = wx.Notebook(self)
        self.notebook.SetBackgroundColour(theme.BG_CARD)
        self.overview = ResultBox(self.notebook, min_height=160)
        self.deps_list = wx.ListCtrl(
            self.notebook,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
        )
        self.issues_ctrl = ResultBox(self.notebook, min_height=160)
        self.obligations_ctrl = ResultBox(self.notebook, min_height=120)
        self.prolog_ctrl = ResultBox(self.notebook, min_height=120)
        self.notebook.AddPage(self.overview, "Overview")
        self.notebook.AddPage(self.deps_list, "Dependencies")
        self.notebook.AddPage(self.issues_ctrl, "Issues & risks")
        self.notebook.AddPage(self.obligations_ctrl, "Obligations")
        self.notebook.AddPage(self.prolog_ctrl, "Prolog")
        self._setup_deps_columns()

        root.Add(self.notebook, 1, wx.EXPAND | wx.ALL, theme.PADDING)
        self.SetSizer(root)

    def _setup_deps_columns(self) -> None:
        self.deps_list.AppendColumn("Package", width=180)
        self.deps_list.AppendColumn("License", width=200)
        self.deps_list.AppendColumn("Confidence", width=100)
        self.deps_list.AppendColumn("Tier", width=90)
        self.deps_list.SetBackgroundColour(theme.BG_INPUT)

    def _on_browse(self, event: wx.CommandEvent) -> None:
        dlg = wx.DirDialog(self, "Choose project root")
        if dlg.ShowModal() == wx.ID_OK:
            self._project_path = Path(dlg.GetPath())
            self.path_ctrl.SetValue(str(self._project_path))
        dlg.Destroy()

    def _on_scan(self, event: wx.CommandEvent) -> None:
        if not self._project_path or not self._project_path.is_dir():
            wx.MessageBox("Select a project folder first.", APP_TITLE, wx.OK | wx.ICON_WARNING)
            return
        self.scan_btn.Disable()
        self.status.SetLabel("Scanning project…")
        self.notebook.SetSelection(0)

        def work() -> None:
            try:
                report = self._service.analyze(self._project_path)
            except Exception as exc:
                wx.CallAfter(self._show_error, str(exc))
                return
            wx.CallAfter(self._show_report, report)

        threading.Thread(target=work, daemon=True).start()

    def _show_error(self, msg: str) -> None:
        self.overview.SetValue(f"Scan failed\n{'─' * 24}\n{msg}")
        self.status.SetLabel("Error during scan.")
        self.scan_btn.Enable()

    def _show_report(self, report: ComplianceReport) -> None:
        self._report = report
        risk = report.overall_risk.value
        self.risk_badge.SetLabel(f"Overall risk: {risk.upper()}")
        self.risk_badge.SetForegroundColour(theme.risk_colour(risk))
        self.overview.SetValue(self._format_overview(report))
        self._fill_deps(report)
        self.issues_ctrl.SetValue(self._format_issues(report))
        self.obligations_ctrl.SetValue(
            "\n".join(f"• {o}" for o in report.obligations) or "No obligations listed."
        )
        self.prolog_ctrl.SetValue(
            report.prolog_reasoning_summary or "Prolog engine not available."
        )
        self.status.SetLabel(
            f"Complete — {report.files_scanned} findings, {len(report.issues)} issues."
        )
        self.scan_btn.Enable()
        self.export_json_btn.Enable()
        self.export_md_btn.Enable()

    def _fill_deps(self, report: ComplianceReport) -> None:
        self.deps_list.DeleteAllItems()
        for dep in report.dependencies:
            lic = dep.declared_license
            idx = self.deps_list.InsertItem(self.deps_list.GetItemCount(), dep.name)
            if lic:
                self.deps_list.SetItem(idx, 1, lic.display_name)
                self.deps_list.SetItem(idx, 2, f"{lic.confidence:.0%}")
                self.deps_list.SetItem(idx, 3, lic.confidence_tier.value)
            else:
                self.deps_list.SetItem(idx, 1, "Unknown")
                self.deps_list.SetItem(idx, 2, "—")
                self.deps_list.SetItem(idx, 3, "unknown")

    @staticmethod
    def _format_overview(report: ComplianceReport) -> str:
        lines = [report.summary(), ""]
        if report.project_license:
            pl = report.project_license
            lines.append(f"Detection: {pl.detection_method} ({pl.confidence_tier.value})")
        lines.append("")
        for a in report.recommended_actions:
            lines.append(f"→ {a}")
        return "\n".join(lines)

    @staticmethod
    def _format_issues(report: ComplianceReport) -> str:
        if not report.issues:
            return "No compliance issues flagged."
        parts = []
        for issue in report.issues:
            parts.append(f"[{issue.severity.value.upper()}] {issue.title}")
            parts.append(issue.description)
            parts.append(f"Recommendation: {issue.recommendation}")
            if issue.prolog_explanation:
                parts.append(f"Prolog: {issue.prolog_explanation}")
            parts.append("")
        return "\n".join(parts)

    def _on_export_json(self, event: wx.CommandEvent) -> None:
        if not self._report:
            return
        dlg = wx.FileDialog(
            self, "Save JSON report", wildcard="JSON (*.json)|*.json", style=wx.FD_SAVE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            export_json(self._report, Path(dlg.GetPath()))
        dlg.Destroy()

    def _on_export_md(self, event: wx.CommandEvent) -> None:
        if not self._report:
            return
        dlg = wx.FileDialog(
            self, "Save Markdown report", wildcard="Markdown (*.md)|*.md", style=wx.FD_SAVE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            export_markdown(self._report, Path(dlg.GetPath()))
        dlg.Destroy()
