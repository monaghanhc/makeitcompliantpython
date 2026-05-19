"""Project compliance scanner UI with tabbed report and export."""

from __future__ import annotations

import threading
from pathlib import Path

import wx

from makeitcompliant.app.core.compliance_models import ComplianceReport
from makeitcompliant.app.core.project_compliance import ProjectComplianceService
from makeitcompliant.app.core.report_builder import export_json, export_markdown
from makeitcompliant.app.gui.styles import APP_TITLE, body_font, header_font


class ProjectScanPanel(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent=parent)
        self._service = ProjectComplianceService()
        self._project_path: Path | None = None
        self._report: ComplianceReport | None = None

        title = wx.StaticText(self, label="Project Compliance Scanner")
        title.SetFont(header_font())
        subtitle = wx.StaticText(
            self,
            label="ML license detection + SWI-Prolog compatibility reasoning.",
        )
        subtitle.SetFont(body_font())
        subtitle.Wrap(600)

        self.path_ctrl = wx.TextCtrl(self, style=wx.TE_READONLY)
        browse = wx.Button(self, label="Select Folder…")
        browse.Bind(wx.EVT_BUTTON, self._on_browse)
        self.scan_btn = wx.Button(self, label="Analyze Compliance")
        self.scan_btn.Bind(wx.EVT_BUTTON, self._on_scan)
        self.export_json_btn = wx.Button(self, label="Export JSON")
        self.export_json_btn.Bind(wx.EVT_BUTTON, self._on_export_json)
        self.export_md_btn = wx.Button(self, label="Export Markdown")
        self.export_md_btn.Bind(wx.EVT_BUTTON, self._on_export_md)
        self.export_json_btn.Disable()
        self.export_md_btn.Disable()

        self.status = wx.StaticText(self, label="Ready.")
        self.risk_badge = wx.StaticText(self, label="Risk: —")
        self.risk_badge.SetFont(header_font())

        self.notebook = wx.Notebook(self)
        self.overview = wx.TextCtrl(self.notebook, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.deps_list = wx.ListCtrl(
            self.notebook, style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
        )
        self.issues_ctrl = wx.TextCtrl(self.notebook, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.obligations_ctrl = wx.TextCtrl(self.notebook, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.prolog_ctrl = wx.TextCtrl(self.notebook, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.notebook.AddPage(self.overview, "Overview")
        self.notebook.AddPage(self.deps_list, "Dependencies")
        self.notebook.AddPage(self.issues_ctrl, "Issues & risks")
        self.notebook.AddPage(self.obligations_ctrl, "Obligations")
        self.notebook.AddPage(self.prolog_ctrl, "Prolog / explain")

        self._setup_deps_columns()

        path_row = wx.BoxSizer(wx.HORIZONTAL)
        path_row.Add(self.path_ctrl, 1, wx.EXPAND | wx.RIGHT, 6)
        path_row.Add(browse, 0)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        btn_row.Add(self.scan_btn, 0, wx.RIGHT, 6)
        btn_row.Add(self.export_json_btn, 0, wx.RIGHT, 6)
        btn_row.Add(self.export_md_btn, 0)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(title, 0, wx.ALL, 6)
        root.Add(subtitle, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        root.Add(path_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        root.Add(btn_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        root.Add(self.status, 0, wx.LEFT | wx.RIGHT, 4)
        root.Add(self.risk_badge, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        root.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 6)
        self.SetSizer(root)

    def _setup_deps_columns(self) -> None:
        self.deps_list.AppendColumn("Package", width=160)
        self.deps_list.AppendColumn("License", width=180)
        self.deps_list.AppendColumn("Confidence", width=90)
        self.deps_list.AppendColumn("Tier", width=80)

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
                report = None
                wx.CallAfter(self._show_error, str(exc))
                return
            wx.CallAfter(self._show_report, report)

        threading.Thread(target=work, daemon=True).start()

    def _show_error(self, msg: str) -> None:
        self.overview.SetValue(f"Scan failed:\n{msg}")
        self.status.SetLabel("Error.")
        self.scan_btn.Enable()

    def _show_report(self, report: ComplianceReport) -> None:
        self._report = report
        self.risk_badge.SetLabel(f"Overall risk: {report.overall_risk.value.upper()}")
        self.overview.SetValue(self._format_overview(report))
        self._fill_deps(report)
        self.issues_ctrl.SetValue(self._format_issues(report))
        self.obligations_ctrl.SetValue("\n".join(f"• {o}" for o in report.obligations) or "None")
        self.prolog_ctrl.SetValue(report.prolog_reasoning_summary or "Prolog engine not available.")
        self.status.SetLabel(
            f"Done — {report.files_scanned} findings, {len(report.issues)} issues."
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
            self, "Save JSON report", wildcard="JSON (*.json)|*.json", style=wx.FD_SAVE
        )
        if dlg.ShowModal() == wx.ID_OK:
            export_json(self._report, Path(dlg.GetPath()))
        dlg.Destroy()

    def _on_export_md(self, event: wx.CommandEvent) -> None:
        if not self._report:
            return
        dlg = wx.FileDialog(
            self, "Save Markdown report", wildcard="Markdown (*.md)|*.md", style=wx.FD_SAVE
        )
        if dlg.ShowModal() == wx.ID_OK:
            export_markdown(self._report, Path(dlg.GetPath()))
        dlg.Destroy()
