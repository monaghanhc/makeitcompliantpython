const SPDX_RE = /SPDX-License-Identifier:\s*([A-Za-z0-9.-]+)/i;

const SPDX_MAP = {
  MIT: "MIT (permissive)",
  "Apache-2.0": "Apache License 2.0 (permissive)",
  "GPL-3.0-only": "GPL-3.0 (strong copyleft)",
  "GPL-2.0-only": "GPL-2.0 (strong copyleft)",
  "LGPL-3.0-only": "LGPL-3.0 (weak copyleft)",
  "AGPL-3.0-only": "AGPL-3.0 (network copyleft)",
  "BSD-2-Clause": "BSD 2-Clause",
  "BSD-3-Clause": "BSD 3-Clause",
  "MPL-2.0": "Mozilla Public License 2.0",
  ISC: "ISC License",
  Unlicense: "The Unlicense",
};

document.getElementById("detectBtn").addEventListener("click", () => {
  const text = document.getElementById("licenseInput").value;
  const out = document.getElementById("demoResult");
  const m = text.match(SPDX_RE);
  if (!m) {
    out.textContent =
      "No SPDX-License-Identifier found.\n\nFull TF-IDF + Prolog analysis runs in the desktop app only.";
    return;
  }
  const id = m[1];
  const label = SPDX_MAP[id] || "Recognized SPDX ID (see desktop app for full rules)";
  out.textContent = `SPDX: ${id}\nClassification: ${label}\nConfidence: high (identifier match)\n\nThis demo does not run SWI-Prolog or ML template matching in the browser.`;
});
