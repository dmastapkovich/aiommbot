#!/usr/bin/env python3
"""check-index: every document in a typed directory is listed in that directory's index.

Usage: check-index.py [<paths>...]

Only the typed directories under the paths given are checked. If none are
given, every one of them is.

docs/documentation-style.md §6 states the rule this mechanises: "Every index
(README.md) lists every document in its directory. An unindexed document does
not exist." The failure it catches is silent -- the file is committed, the
links into it resolve, `check-docs.py` passes, and nobody navigating the
catalogue ever arrives at it.

The check runs one way. A file in a typed directory must be the target of a
relative link in that directory's README.md. An index row that names a file
not yet committed is legal (§6 lets a planned document hold a row, naming the
file in a code span until it is linked), and a link to a file that is missing
is already `check-docs.py --links`.

Which directories are typed is a declaration, not a discovery, because the
repository root carries a README.md that addresses a visitor rather than a
catalogue reader: a rule that read every README.md as an index would report
six findings there on its first run. Every directory holding a tracked *.md is
therefore either INDEXED or named in UNINDEXED with its reason, and one that is
neither is itself a finding -- so a new document type cannot be added without
deciding which it is.

Exit codes: 0 no findings, 1 findings reported, 2 bad usage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _markdown import ABSOLUTE, LINK, REPO, markdown_files, prose

INDEXED = (
    ".agents/research",
    "docs",
    "docs/adr",
    "docs/design",
    "docs/design/components",
    "docs/research",
)
"""The typed directories of docs/documentation-style.md §1, each with an index."""

UNINDEXED = {
    ".": "README.md addresses a visitor to the repository, not a reader of the catalogue",
    ".agents": "AGENTS.md, *Where things live*, is where a process document is found",
    ".agents/skills": "a skill is loaded by name, never navigated to",
    ".github": "GitHub reads these files by path; nothing navigates to them",
}
"""Directories that hold Markdown and owe no index, each with the reason it owes none."""


def declared(directory: str) -> str | None:
    """The reason `directory` owes no index, or None if it is not declared.

    The longest declaration wins, so `.agents/skills` states its own reason
    rather than inheriting the one `.agents` gives.
    """
    matching = [
        prefix
        for prefix in UNINDEXED
        if directory == prefix or (prefix != "." and directory.startswith(f"{prefix}/"))
    ]
    return UNINDEXED[max(matching, key=len)] if matching else None


def listed(index: Path) -> set[str]:
    """Every file name the index links to, relative to its own directory."""
    lines = index.read_text(encoding="utf-8").split("\n")
    names = set()
    for line in prose(lines):
        for match in LINK.finditer(line):
            target = match.group(1)
            if not target.startswith(ABSOLUTE):
                names.add(target.partition("#")[0])
    return names


def check(directory: str, files: list[Path]) -> tuple[list[str], int]:
    """Findings for one typed directory, and the number of documents it indexes."""
    index = REPO / directory / "README.md"
    if not index.exists():
        return [f"{directory}/README.md: a typed directory has no index"], 0
    names = listed(index)
    documents = [path for path in files if path.name != "README.md"]
    missing = [path.name for path in documents if path.name not in names]
    findings = [
        f"{directory}/README.md: {name} is in this directory and not in this index"
        for name in sorted(missing)
    ]
    return findings, len(documents)


def main(argv: list[str] | None = None) -> int:
    """Check every typed directory under the requested paths."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", default=[])
    args = parser.parse_args(argv)

    holding: dict[str, list[Path]] = {}
    for path in markdown_files(args.paths):
        holding.setdefault(str(path.parent.relative_to(REPO)), []).append(path)

    findings: list[str] = []
    counted: list[tuple[str, int]] = []
    exempt: list[tuple[str, str]] = []
    for directory in sorted(holding):
        if directory in INDEXED:
            found, documents = check(directory, holding[directory])
            findings += found
            counted.append((directory, documents))
            continue
        reason = declared(directory)
        if reason is None:
            findings.append(
                f"{directory}: holds Markdown and is neither a typed directory nor "
                f"declared in UNINDEXED; decide which it is"
            )
        else:
            exempt.append((directory, reason))

    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    # Name what was checked and what was exempted, or a maintainer reading a
    # green line cannot tell an index that is complete from one that was skipped.
    total = sum(documents for _, documents in counted)
    print(f"check-index: {total} documents indexed across {len(counted)} typed directories")
    for directory, documents in counted:
        print(f"             {directory}: {documents}")
    for directory, reason in exempt:
        print(f"             {directory}: no index -- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
