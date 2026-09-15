#!/usr/bin/env python3
"""check-docs: check every Markdown file against docs/documentation-style.md.

Usage: check-docs.py [--width | --links] [<paths>...]

Only the paths given are checked. If none are given, every tracked *.md is.
Use "--width" or "--links" to run one family of checks alone.

Three checks, mechanising two lines of .agents/design-quality-checklist.md:

    width     a line over 100 columns that a rewrap could bring under it (§8)
    links     a relative link whose target file does not exist (§6)
    anchors   a relative link whose #fragment matches no heading there (§6)

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
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

WIDTH = 100
"""Columns of prose, from docs/documentation-style.md §8."""

EXEMPT_WIDTH = ("docs/research/", ".agents/research/")
"""Path prefixes the width check skips; every other tracked file is checked."""

RECORD_ROW = re.compile(r"- \[[ x]\] |_[A-Z]")
"""A line holding one record: a checklist row, or a rulebook field such as `_Tier:_`."""

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(?:(?!\1).)*?\1(?!`)", re.DOTALL)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
ABSOLUTE = ("http://", "https://", "mailto:", "//")


def markdown_files(paths: list[str]) -> list[Path]:
    """Every tracked *.md under the given paths, or under the repository root."""
    argv = ["git", "-C", str(REPO), "ls-files", "-z", "--", *(paths or ["*.md"])]
    listing = subprocess.run(argv, capture_output=True, text=True, check=True).stdout
    return sorted(REPO / name for name in listing.split("\0") if name.endswith(".md"))


def body(lines: list[str]) -> list[str]:
    """The file with fenced blocks and front matter blanked, numbering preserved."""
    kept: list[str] = []
    fence: str | None = None
    front = bool(lines) and lines[0].strip() == "---"
    for number, line in enumerate(lines, start=1):
        if front:
            front = not (number > 1 and line.strip() == "---")
            kept.append("")
            continue
        edge = FENCE.match(line)
        if fence is None and edge:
            fence = edge.group(1)[0]
            kept.append("")
            continue
        if fence is not None:
            if edge and edge.group(1)[0] == fence:
                fence = None
            kept.append("")
            continue
        kept.append(line)
    return kept


def prose(lines: list[str]) -> list[str]:
    """`body` with inline code spans blanked, so a quoted link is not read as one."""
    blanked = CODE_SPAN.sub(lambda m: " " * len(m.group(0)), "\n".join(body(lines)))
    return blanked.split("\n")


def slug(heading: str) -> str:
    """GitHub's heading anchor: link text kept, punctuation dropped, spaces hyphenated."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).replace("`", "").lower()
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", text).strip())


def anchors(lines: list[str]) -> set[str]:
    """Every anchor the file offers; a repeated slug takes GitHub's `-1`, `-2` suffix."""
    seen: Counter[str] = Counter()
    found: set[str] = set()
    for line in body(lines):
        heading = HEADING.match(line)
        if heading:
            base = slug(heading.group(2))
            found.add(base if not seen[base] else f"{base}-{seen[base]}")
            seen[base] += 1
    return found


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
    text = {path: path.read_text(encoding="utf-8").split("\n") for path in files}
    index = {path.resolve(): anchors(lines) for path, lines in text.items()}

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
