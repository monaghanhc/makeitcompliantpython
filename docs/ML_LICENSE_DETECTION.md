# ML License Detection

## Pipeline (local, lightweight)

1. **SPDX detection** (`ml/spdx_detector.py`) — fastest; scans for `SPDX-License-Identifier:` lines.
2. **TF-IDF cosine similarity** (`ml/license_detector.py`) — compares normalized text to cached templates in `license_templates/`.
3. **Unknown** — if best score &lt; 0.70, identifier is `unknown` (needs manual review).

## Confidence tiers

| Score | Tier | Meaning |
|-------|------|---------|
| ≥ 0.90 | high | Strong template or SPDX match |
| 0.70 – 0.89 | medium | Likely match; verify |
| &lt; 0.70 | unknown | Do not auto-apply |

## Caching

- `ml/model_cache.py` loads all templates once per process.
- NLTK `punkt` / `punkt_tab` downloaded on first tokenization.

## Modules

| File | Role |
|------|------|
| `normalizer.py` | Text normalization |
| `spdx_detector.py` | SPDX heuristics |
| `license_detector.py` | Main `LicenseDetector.detect()` API |
| `classifier.py` | Legacy wrapper for `FileComparison` |
| `features.py` | TF-IDF + Jaccard |

## Optional training

`train_model.py` is not required for production; the default is unsupervised template matching. A linear classifier can be added later under `ml/training_data/` if labeled data grows.

## Design rule

**ML detects; Prolog reasons.** Do not encode compatibility law in the ML layer.
