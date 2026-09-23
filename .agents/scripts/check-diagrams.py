#!/usr/bin/env python3
"""check-diagrams: every Mermaid diagram in the catalogue parses.

Usage: check-diagrams.py [<paths>...]

Only the paths given are checked. If none are given, every tracked *.md is.

docs/design/diagrams.md makes Mermaid the only diagram language, and a
diagram that does not parse fails in the reader's browser rather than in
the build: GitHub renders each fenced block in a cross-origin iframe
(.agents/research/38-mermaid-sequence-diagram-limits.md), so a syntax
error is invisible to everything upstream of the reader. This is the
check that makes the noise instead.

No project in the reference corpus validates Mermaid in CI -- 20 of the
93 clones ship a Mermaid diagram (a ```mermaid or ```{mermaid} fence, a
`.. mermaid::` directive, or a .mmd source) and none parses one, across
656 workflow files and 48 pre-commit configurations. This check is ours rather
than borrowed, and it is built the only way the corpus leaves open: the
renderer itself, run headless. The shape is taken from
koxudaxi/datamodel-code-generator, which drives the same binary through
Puppeteer with a no-sandbox configuration file.

Each block is parsed on its own, so a finding names the line the diagram
starts on rather than the file that holds eight of them. The cost is one
headless browser per diagram; the workflow budgets for it.

Blocks are found with the repository's own Markdown parser, not with a
line-anchored pattern, because the catalogue quotes Mermaid as often as
it draws it: a fence inside a blockquote inside a wider fence, and a
four-backtick code span naming the language, are both quotations and
neither is a diagram.

Exit codes: 0 no findings, 1 findings reported, 2 mmdc is unavailable.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _markdown import REPO, fences, markdown_files

PUPPETEER = Path(__file__).resolve().parent / "puppeteer-no-sandbox.json"
"""Chromium cannot open its own sandbox on a CI runner; this is how koxudaxi passes."""


def blocks(lines: list[str]) -> list[tuple[int, str]]:
    """Every Mermaid block: the line its fence opens on, and its source."""
    found = []
    starts = [line for info, line in fences(lines) if info.lower() == "mermaid"]
    for start in starts:
        source = []
        for line in lines[start:]:
            if line.strip().startswith(("```", "~~~")):
                break
            source.append(line)
        found.append((start, "\n".join(source)))
    return found


CANARY = "flowchart LR\n  a --> b\n"
"""A diagram that certainly parses, rendered first to tell a broken renderer from a broken diagram."""


def render(source: str, mmdc: str, scratch: Path) -> str | None:
    """The renderer's complaint about one diagram, or None when it parses."""
    diagram = scratch / "diagram.mmd"
    diagram.write_text(source, encoding="utf-8")
    argv = [
        mmdc,
        "--input", str(diagram),
        "--output", str(scratch / "diagram.svg"),
        "--puppeteerConfigFile", str(PUPPETEER),
        "--quiet",
    ]
    done = subprocess.run(argv, capture_output=True, text=True)
    if done.returncode == 0:
        return None
    # The first line that carries the error; the rest of stderr is a stack trace
    # through puppeteer, which names its own files rather than the diagram.
    for line in done.stderr.split("\n"):
        text = line.strip()
        if text and not text.startswith("at "):
            return text
    return f"mmdc exited {done.returncode}"


def main(argv: list[str] | None = None) -> int:
    """Parse every Mermaid block under the requested paths."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", default=[])
    args = parser.parse_args(argv)

    mmdc = shutil.which("mmdc")
    if mmdc is None:
        print(
            "check-diagrams: mmdc is not on PATH. Install @mermaid-js/mermaid-cli, "
            "or let the diagrams workflow run this check.",
            file=sys.stderr,
        )
        return 2

    findings: list[str] = []
    drawn = 0
    files = 0
    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        # Render a diagram that cannot fail first. Without it a renderer that
        # never starts -- no browser downloaded, no sandbox to open one in --
        # reports every diagram in the catalogue as broken, which is a lie
        # that looks exactly like the defect this check exists to find.
        broken = render(CANARY, mmdc, scratch)
        if broken:
            print(f"check-diagrams: the Mermaid renderer did not start: {broken}", file=sys.stderr)
            return 2
        for path in markdown_files(args.paths):
            lines = path.read_text(encoding="utf-8").split("\n")
            diagrams = blocks(lines)
            if not diagrams:
                continue
            files += 1
            drawn += len(diagrams)
            for start, source in diagrams:
                complaint = render(source, mmdc, scratch)
                if complaint:
                    findings.append(f"{path.relative_to(REPO)}:{start}: {complaint}")

    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    print(f"check-diagrams: {drawn} diagrams in {files} files parse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
