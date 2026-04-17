#!/usr/bin/env python3
"""Render Mermaid .mmd files to PNG via @mermaid-js/mermaid-cli.

Sizing is auto-picked from each diagram's first directive:
  C4Context        -> 1092x1092 (square sweet spot)
  C4Container      -> 1500x900  (wide)
  C4Component      -> 1500x900  (wide)
  sequenceDiagram  -> 900x1500  (tall)
  anything else    -> 1200x900  (mixed default)

Override with WIDTH / HEIGHT env vars (applied to every file when set).

Usage:
  render.py <file.mmd>    # renders one file to <file>.png alongside it
  render.py <dir>         # renders every .mmd in <dir> to matching .png

Env overrides:
  WIDTH, HEIGHT, BG (default white), THEME (default default)

Behavior on failure: best-effort batch. Continues past per-file errors,
reports a summary at the end, exits 1 if any file failed.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BG = os.environ.get("BG", "white")
THEME = os.environ.get("THEME", "default")
USER_WIDTH = os.environ.get("WIDTH", "")
USER_HEIGHT = os.environ.get("HEIGHT", "")

DIRECTIVE_RE = re.compile(
    r"^\s*(C4Context|C4Container|C4Component|sequenceDiagram|flowchart|graph"
    r"|stateDiagram|classDiagram|erDiagram|gantt|pie|journey)\b"
)

SIZE_MAP = {
    "C4Context": (1092, 1092),
    "C4Container": (1500, 900),
    "C4Component": (1500, 900),
    "sequenceDiagram": (900, 1500),
}
DEFAULT_SIZE = (1200, 900)


def first_directive(src: Path) -> str | None:
    try:
        with src.open() as f:
            for line in f:
                m = DIRECTIVE_RE.match(line)
                if m:
                    return m.group(1)
    except OSError:
        return None
    return None


def pick_size(src: Path) -> tuple[int, int]:
    if USER_WIDTH and USER_HEIGHT:
        return int(USER_WIDTH), int(USER_HEIGHT)
    return SIZE_MAP.get(first_directive(src) or "", DEFAULT_SIZE)


def pick_mmdc() -> list[str]:
    if shutil.which("mmdc"):
        return ["mmdc"]
    return ["npx", "-y", "-p", "@mermaid-js/mermaid-cli", "mmdc"]


def render_one(src: Path, mmdc: list[str], failures: list[str]) -> None:
    if not src.is_file():
        print(f"not a file: {src}", file=sys.stderr)
        failures.append(f"{src} (not found)")
        return
    out = src.with_suffix(".png")
    w, h = pick_size(src)
    print(f"rendering {src} -> {out} ({w}x{h})")
    try:
        proc = subprocess.run(
            mmdc + ["-i", str(src), "-o", str(out),
                    "-w", str(w), "-H", str(h), "-b", BG, "-t", THEME],
            check=False,
        )
        if proc.returncode != 0:
            failures.append(f"{src} (mmdc failed)")
            return
    except OSError as e:
        failures.append(f"{src} (mmdc error: {e})")
        return


USAGE = """\
usage: render.py <file.mmd | dir>

Sizing is auto-picked from each diagram's first directive
(C4Context/Container/Component, sequenceDiagram, ...). Override with env:
  WIDTH=, HEIGHT=, BG=white, THEME=default

For rationale and per-diagram-type optima, see references/vision-image-sizing.md
"""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write(USAGE)
        return 2

    target = Path(argv[1])
    mmdc = pick_mmdc()
    failures: list[str] = []

    if target.is_file():
        render_one(target, mmdc, failures)
    elif target.is_dir():
        files = sorted(target.glob("*.mmd"))
        if not files:
            print(f"no .mmd files in {target}", file=sys.stderr)
            return 1
        for f in files:
            render_one(f, mmdc, failures)
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
