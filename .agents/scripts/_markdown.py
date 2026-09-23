"""The Markdown reading the catalogue checkers share.

One parser, so `check-docs.py`, `check-index.py` and `check-diagrams.py`
agree on what a fenced block is. Each checker does one job; none of them
re-derives where a code fence opens, because three parsers disagree and
the disagreement is silent -- a checker that mistakes a line for a fence
skips everything until it finds a closing one, and reports nothing.

Fences follow CommonMark 4.5: a run of three or more backticks or
tildes, closed by a run of the same character at least as long. A
backtick fence's info string may not contain a backtick, which is what
keeps an inline code span written with four backticks from opening a
block that swallows the lines after it.
https://spec.commonmark.org/0.31.2/#fenced-code-blocks
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(?:(?!\1).)*?\1(?!`)", re.DOTALL)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ABSOLUTE = ("http://", "https://", "mailto:", "//")


def markdown_files(paths: list[str]) -> list[Path]:
    """Every tracked *.md under the given paths, or under the repository root."""
    argv = ["git", "-C", str(REPO), "ls-files", "-z", "--", *(paths or ["*.md"])]
    listing = subprocess.run(argv, capture_output=True, text=True, check=True).stdout
    return sorted(REPO / name for name in listing.split("\0") if name.endswith(".md"))


def _opens(line: str) -> tuple[str, str] | None:
    """The fence a line opens -- its marker and info string -- or None."""
    edge = FENCE.match(line)
    if edge is None:
        return None
    marker, info = edge.group(1), edge.group(2)
    if marker[0] == "`" and "`" in info:
        return None  # An info string with a backtick is a code span, not a fence.
    return marker, info


def _closes(line: str, marker: str) -> bool:
    """Whether a line closes the fence opened by `marker`.

    A closing fence carries no info string (CommonMark 4.5). Without that
    clause a line inside the block that merely starts with enough backticks
    ends it, the real closer then opens a phantom block, and everything after
    it is blanked -- which is to say checked by nothing.
    """
    edge = FENCE.match(line)
    if edge is None:
        return False
    same = edge.group(1)[0] == marker[0] and len(edge.group(1)) >= len(marker)
    return same and not edge.group(2).strip()


def fences(lines: list[str]):
    """Every fenced block: its info string, and the line its content starts on."""
    marker: str | None = None
    for number, line in enumerate(lines, start=1):
        if marker is None:
            edge = _opens(line)
            if edge:
                marker = edge[0]
                yield edge[1].strip(), number
            continue
        if _closes(line, marker):
            marker = None


def body(lines: list[str]) -> list[str]:
    """The file with fenced blocks and front matter blanked, numbering preserved."""
    kept: list[str] = []
    marker: str | None = None
    front = bool(lines) and lines[0].strip() == "---"
    for number, line in enumerate(lines, start=1):
        if front:
            front = not (number > 1 and line.strip() == "---")
            kept.append("")
            continue
        if marker is None:
            edge = _opens(line)
            if edge:
                marker = edge[0]
                kept.append("")
                continue
            kept.append(line)
            continue
        if _closes(line, marker):
            marker = None
        kept.append("")
    return kept


def _blank(match: re.Match[str]) -> str:
    """The match, every character but a newline replaced by a space.

    Blanking a newline would join two lines and shift every line number after
    it, so a finding would name the wrong line.
    """
    return re.sub(r"[^\n]", " ", match.group(0))


def prose(lines: list[str]) -> list[str]:
    """`body` with inline code spans blanked, so a quoted link is not read as one.

    A code span is inline, so it cannot cross a blank line. Matching over the
    whole file instead lets one unbalanced backtick pair with the next one
    anywhere below it and blank every link in between.
    """
    blanked = [
        chunk if not chunk.strip() else CODE_SPAN.sub(_blank, chunk)
        for chunk in re.split(r"(\n[ \t]*\n)", "\n".join(body(lines)))
    ]
    return "".join(blanked).split("\n")


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
