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
    compat: { gpl: "high risk", apache: "low" },
  },
  {
    id: "Apache-2.0",
    label: "Apache License 2.0 (permissive)",
    family: "permissive",
    patterns: [/SPDX-License-Identifier:\s*Apache-2\.0/i, /Apache License.*2\.0/i],
    compat: { mit: "low", gpl: "high" },
  },
  {
    id: "GPL-3.0",
    label: "GPL-3.0 (strong copyleft)",
    family: "strong_copyleft",
    patterns: [/SPDX-License-Identifier:\s*GPL-3\.0/i, /GNU GENERAL PUBLIC LICENSE.*Version 3/i],
    compat: { mit: "high", proprietary: "critical" },
  },
  {
    id: "AGPL-3.0",
    label: "AGPL-3.0 (network copyleft)",
    family: "strong_copyleft",
    patterns: [/SPDX-License-Identifier:\s*AGPL-3\.0/i, /Affero General Public License/i],
    compat: { mit: "high", saas: "review network obligations" },
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
  const spdx = text.match(SPDX_RE);
  if (spdx) {
    return {
      id: spdx[1],
      label: `SPDX ${spdx[1]}`,
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

document.getElementById("detectBtn").addEventListener("click", () => {
  const text = document.getElementById("licenseInput").value;
  const textB = document.getElementById("licenseInputB").value;
  const out = document.getElementById("demoResult");
  const a = detectLicense(text);
  const b = textB.trim() ? detectLicense(textB) : null;
  let msg = [
    "=== License A ===",
    `ID: ${a.id}`,
    `Label: ${a.label}`,
    `Family: ${a.family}`,
    `Confidence: ${a.confidence}`,
    `Method: ${a.method}`,
  ];
  if (b) {
    msg = msg.concat([
      "",
      "=== License B ===",
      `ID: ${b.id}`,
      `Label: ${b.label}`,
      `Family: ${b.family}`,
      "",
      "=== Prolog-style compatibility (demo) ===",
      prologStyleNote(a, b),
    ]);
  }
  msg.push("", "100% free & open source (MIT). Full analysis: desktop + SWI-Prolog.");
  out.textContent = msg.join("\n");
});
