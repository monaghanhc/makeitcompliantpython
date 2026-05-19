from __future__ import annotations

from pathlib import Path

import pytest

MIT_SNIPPET = """\
SPDX-License-Identifier: MIT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.
"""

GPL3_SNIPPET = """\
SPDX-License-Identifier: GPL-3.0-only

GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007
"""


@pytest.fixture
def mit_text() -> str:
    return MIT_SNIPPET


@pytest.fixture
def gpl3_text() -> str:
    return GPL3_SNIPPET


@pytest.fixture
def mit_license_file(tmp_path: Path) -> Path:
    p = tmp_path / "MIT-License.txt"
    p.write_text(MIT_SNIPPET, encoding="utf-8")
    return p


@pytest.fixture
def gpl3_license_file(tmp_path: Path) -> Path:
    p = tmp_path / "GPL-3.txt"
    p.write_text(GPL3_SNIPPET, encoding="utf-8")
    return p
