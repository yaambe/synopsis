#!/usr/bin/env python3
"""Lint Mermaid .mmd files emitted by synopsis sub-agents.

Catches the structural failure modes that produce unusable diagrams:
  - Empty file
  - No recognized first directive (C4Context / C4Container / C4Component / sequenceDiagram / ...)
  - Prose / extra content before the first directive (sub-agent left fence wrappers in)
  - C4Container or C4Component missing UpdateLayoutConfig (renders as a one-box-per-row column)

Does NOT invoke mmdc -- keep this fast. For deeper syntax validation, run
mermaid2png's render.py; mmdc parser errors will surface there.

Usage:
  lint.py <file.mmd>
  lint.py <dir>

Best-effort batch. Continues past per-file failures, prints a summary,
exits 1 if any file failed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DIRECTIVE_RE = re.compile(
    r"^\s*(C4Context|C4Container|C4Component|sequenceDiagram|flowchart|graph"
    r"|stateDiagram|classDiagram|erDiagram)\b"
)

# Lines allowed to appear before the directive: blank, mermaid comment (%%),
# or YAML-ish frontmatter fence (---).
PRE_DIRECTIVE_SKIP = re.compile(r"^\s*$|^\s*%%|^\s*---")


def lint_one(src: Path, failures: list[str]) -> None:
    if not src.is_file():
        print(f"not a file: {src}", file=sys.stderr)
        failures.append(f"{src}: not found")
        return

    try:
        text = src.read_text()
    except OSError as e:
        failures.append(f"{src}: read error: {e}")
        return

    if not text.strip():
        failures.append(f"{src}: empty file")
        return

    first = None
    first_line_idx = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = DIRECTIVE_RE.match(line)
        if m:
            first = m.group(1)
            first_line_idx = i
            break

    if not first:
        failures.append(
            f"{src}: no recognized first directive "
            "(expected C4Context / C4Container / C4Component / sequenceDiagram / ...)"
        )
        return

    pre_junk = [
        line for line in lines[:first_line_idx]
        if not PRE_DIRECTIVE_SKIP.match(line)
    ]
    if pre_junk:
        failures.append(
            f"{src}: non-mermaid content before first directive "
            "— sub-agent likely left a code fence or prose in"
        )
        return

    if first in ("C4Container", "C4Component") and "UpdateLayoutConfig" not in text:
        failures.append(
            f"{src}: {first} missing UpdateLayoutConfig "
            "— Mermaid will render one box per row"
        )
        return

    print(f"ok: {src} ({first})")


USAGE = """\
usage: lint.py <file.mmd | dir>

Structural well-formedness checks; no mmdc invocation. For deeper validation,
render with mermaid2png and watch for parser errors.
"""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write(USAGE)
        return 2

    target = Path(argv[1])
    failures: list[str] = []

    if target.is_file():
        lint_one(target, failures)
    elif target.is_dir():
        files = sorted(target.glob("*.mmd"))
        if not files:
            print(f"no .mmd files in {target}", file=sys.stderr)
            return 1
        for f in files:
            lint_one(f, failures)
    else:
        print(f"not a file or directory: {target}", file=sys.stderr)
        return 1

    if failures:
        print("", file=sys.stderr)
        print(f"FAILED ({len(failures)}):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
