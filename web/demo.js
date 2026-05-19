/**
 * Client-side SPDX + keyword heuristics (free, no server).
 * Full TF-IDF + SWI-Prolog runs in the free desktop app only.
 */
const SPDX_RE = /SPDX-License-Identifier:\s*([A-Za-z0-9.-]+)/gi;

const RULES = [
  {
    id: "MIT",
    label: "MIT License (permissive)",
    family: "permissive",
    patterns: [/SPDX-License-Identifier:\s*MIT/i, /\bMIT License\b/i],
  },
  {
    id: "Apache-2.0",
    label: "Apache License 2.0 (permissive)",
    family: "permissive",
    patterns: [/SPDX-License-Identifier:\s*Apache-2\.0/i, /Apache License.*2\.0/i],
  },
  {
    id: "GPL-3.0",
    label: "GPL-3.0 (strong copyleft)",
    family: "strong_copyleft",
    patterns: [/SPDX-License-Identifier:\s*GPL-3\.0/i, /GNU GENERAL PUBLIC LICENSE.*Version 3/i],
  },
  {
    id: "AGPL-3.0",
    label: "AGPL-3.0 (network copyleft)",
    family: "strong_copyleft",
    patterns: [/SPDX-License-Identifier:\s*AGPL-3\.0/i, /Affero General Public License/i],
  },
];

function detectLicense(text) {
  for (const rule of RULES) {
    for (const p of rule.patterns) {
      if (p.test(text)) {
        return { ...rule, confidence: "high", method: "pattern" };
      }
    }
  }
  const spdx = [...text.matchAll(SPDX_RE)];
  if (spdx.length) {
    return {
      id: spdx[0][1],
      label: "SPDX " + spdx[0][1],
      family: "see desktop app",
      confidence: "high",
      method: "spdx",
    };
  }
  return {
    id: "unknown",
    label: "Unknown — use desktop app for TF-IDF + Prolog",
    family: "unknown",
    confidence: "low",
    method: "none",
  };
}

function prologStyleNote(a, b) {
  if (!a || !b || a.id === "unknown" || b.id === "unknown") {
    return "Run the free desktop app with SWI-Prolog for rule-based compatibility.";
  }
  if (a.family === "permissive" && b.family === "strong_copyleft") {
    return (
      "Prolog rule (simplified): permissive + strong copyleft → often HIGH risk " +
      "(combined work may trigger copyleft)."
    );
  }
  if (a.family === "permissive" && b.family === "permissive") {
    return "Prolog rule (simplified): permissive + permissive → typically LOW risk.";
  }
  return "See desktop SWI-Prolog engine for analyze_dependency/2.";
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function row(label, value, valueClass) {
  const cls = valueClass ? ' class="' + valueClass + '"' : "";
  return (
    '<p class="result-row"><span>' +
    esc(label) +
    "</span><span" +
    cls +
    ">" +
    esc(value) +
    "</span></p>"
  );
}

function licenseBlock(title, lic) {
  const confClass = lic.confidence === "high" ? "confidence-high" : "confidence-low";
  const parts = [
    '<section class="result-block">',
    "<h4>" + esc(title) + "</h4>",
    row("License", lic.label),
    row("SPDX / ID", lic.id),
    row("Family", lic.family),
    row("Confidence", lic.confidence, confClass),
    row("Method", lic.method),
    "</section>",
  ];
  return parts.join("");
}

document.getElementById("detectBtn").addEventListener("click", () => {
  const text = document.getElementById("licenseInput").value;
  const textB = document.getElementById("licenseInputB").value;
  const out = document.getElementById("demoResult");
  const a = detectLicense(text);
  const b = textB.trim() ? detectLicense(textB) : null;

  let html = licenseBlock("License A", a);
  if (b) {
    html += licenseBlock("License B", b);
    html +=
      '<section class="result-block"><h4>Compatibility (demo)</h4>' +
      '<p class="compat-note">' +
      esc(prologStyleNote(a, b)) +
      "</p></section>";
  }
  html +=
    '<p class="footnote" style="margin-top:1rem">100% free &amp; open source (MIT). ' +
    "Full analysis: desktop + SWI-Prolog.</p>";
  out.innerHTML = html;
});
