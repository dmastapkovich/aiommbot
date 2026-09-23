#!/usr/bin/env python3
"""check-docs: check every Markdown file against docs/documentation-style.md.

Usage: check-docs.py [--width | --links] [<paths>...]

Only the paths given are checked. If none are given, every tracked *.md is.
Use "--width" or "--links" to run one family of checks alone.

Three checks, mechanising two lines of .agents/design-quality-checklist.md:

    width     a line over 100 columns that a rewrap could bring under it (§8)
    links     a relative link whose target file does not exist (§6)
    anchors   a relative link whose #fragment matches no heading there (§6)

Indexes are `check-index.py`; diagrams are `check-diagrams.py`. The
Markdown all three read is `_markdown.py`.

What the width check does not report, and why. §8 states the rule; this is how
each clause of it is recognised.

    fenced blocks, front matter, tables, headings
        §8 exempts them, as do markdownlint MD013's own `code_blocks`,
        `tables` and `headings` parameters.
    a line with no whitespace past column 100
        Nothing can be wrapped narrower than its longest unbreakable run, so
        the finding would not be actionable. This is MD013's default: "This
        rule has an exception when there is no whitespace beyond the
        configured line length. This allows you to include items such as long
        URLs without being forced to break them in the middle."
        https://github.com/DavidAnson/markdownlint/blob/main/doc/md013.md
    a one-record-per-line row (RECORD_ROW)
        A rulebook rule field and a derived review-checklist row hold one
        record each; breaking one splits the record, which is why §8 already
        exempts a table row.
    a research note (EXEMPT_WIDTH)
        A note is evidence, not design: it quotes its sources and is written
        once from primary reading. Reflowing one edits quoted material.

The link and anchor checks exempt nothing, and both blank inline code spans
before matching, because a code span is a quotation rather than a link --
`[name](url)` in a research note names Markdown syntax instead of using it.

Files come from `git ls-files`, so the git-ignored `.refs/` clones are skipped
without naming them here, as is anything not yet added.

Exit codes: 0 no findings, 1 findings reported, 2 bad usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _markdown import ABSOLUTE, LINK, REPO, anchors, body, markdown_files, prose

WIDTH = 100
"""Columns of prose, from docs/documentation-style.md §8."""

EXEMPT_WIDTH = ("docs/research/", ".agents/research/")
"""Path prefixes the width check skips; every other tracked file is checked."""

RECORD_ROW = re.compile(r"- \[[ x]\] |_[A-Z]")
"""A line holding one record: a checklist row, or a rulebook field such as `_Tier:_`."""


def check_width(path: Path, lines: list[str]) -> list[str]:
    """Lines over WIDTH columns that a rewrap could bring under it."""
    findings = []
    for number, line in enumerate(body(lines), start=1):
        text = line.rstrip()
        if len(text) <= WIDTH:
            continue
        stripped = text.lstrip()
        if stripped.startswith(("|", "#")) or RECORD_ROW.match(stripped):
            continue
        if not re.search(r"\s", text[WIDTH:]):
            continue
        findings.append(
            f"{path.relative_to(REPO)}:{number}: {len(text)} columns; wrap at {WIDTH}"
        )
    return findings


def check_links(path: Path, lines: list[str], index: dict[Path, set[str]]) -> list[str]:
    """Relative links whose file is missing, and #fragments that match no heading."""
    findings = []
    for number, line in enumerate(prose(lines), start=1):
        for match in LINK.finditer(line):
            target = match.group(1)
            if target.startswith(ABSOLUTE):
                continue
            name, _, fragment = target.partition("#")
            resolved = (path.parent / name).resolve() if name else path
            where = f"{path.relative_to(REPO)}:{number}: {target}"
            if not resolved.exists():
                findings.append(f"{where}: no such file; name it in a code span instead")
            elif fragment and resolved in index and fragment not in index[resolved]:
                findings.append(f"{where}: no such heading; the target was renumbered")
    return findings


def main(argv: list[str] | None = None) -> int:
    """Run the checks over the requested files and report what they found."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", default=[])
    family = parser.add_mutually_exclusive_group()
    family.add_argument("--width", action="store_true")
    family.add_argument("--links", action="store_true")
    args = parser.parse_args(argv)

    files = markdown_files(args.paths)
    if args.paths and not files:
        print(
            f"check-docs: no tracked Markdown under {' '.join(args.paths)}", file=sys.stderr
        )
        return 2
    text = {path: path.read_text(encoding="utf-8").split("\n") for path in files}
    # Anchors come from the whole catalogue, not from the files being checked, so
    # that running over a subset reports fewer findings rather than weaker ones:
    # a #fragment into a file outside the subset is still resolved.
    index = {
        path.resolve(): anchors(path.read_text(encoding="utf-8").split("\n"))
        for path in markdown_files([])
    }

    findings: list[str] = []
    exempt = 0
    for path, lines in text.items():
        if not args.links:
            if str(path.relative_to(REPO)).startswith(EXEMPT_WIDTH):
                exempt += 1
            else:
                findings += check_width(path, lines)
        if not args.width:
            findings += check_links(path, lines, index)

    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    # Name the exemptions on the green path, so a pass cannot hide a skipped file.
    skipped = "" if args.links else f", {exempt} exempt from the width check"
    print(f"check-docs: {len(files)} files clean{skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
