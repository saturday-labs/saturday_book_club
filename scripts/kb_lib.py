"""Frontmatter I/O and Obsidian wikilink helpers shared by the knowledge_base
schema migration scripts. Pure functions only except read_note/write_note."""

import re
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n?(.*)\Z", re.DOTALL)
_WIKILINK_RE = re.compile(r"^\s*\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]\s*$")


def read_note(path: Path) -> tuple[dict, str]:
    """Split a note into (frontmatter_dict, body_text). Raises ValueError if
    the file has no `---`-delimited frontmatter block."""
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: no frontmatter block found")
    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return frontmatter, body


def write_note(path: Path, frontmatter: dict, body: str) -> None:
    """Write a note back out. Reformats the frontmatter block (PyYAML does
    not preserve original YAML style or comments); leaves body untouched."""
    fm_text = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def normalize_links(value) -> list[str]:
    """Coerce a raw frontmatter field value into a flat list[str]. Handles
    the empty/missing case, a bare scalar, a proper list, and the case where
    an unquoted `[[x]]` in YAML flow context parsed as a nested list
    ([["x"]]) instead of the string "[[x]]"."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(normalize_links(item))
        return out
    return [str(value)]


def link_target(link: str) -> str:
    """Extract the lowercased bare note name a wikilink points at. Accepts
    proper "[[target]]" / "[[target|alias]]" strings, and falls back to
    treating a bracket-less string as the target verbatim (the flattened
    nested-list case from normalize_links)."""
    match = _WIKILINK_RE.match(link)
    target = match.group(1) if match else link
    return target.strip().split("/")[-1].lower()


def merge_links(existing: list[str], incoming: list[str]) -> list[str]:
    """Union two link lists, de-duplicated by link_target (case-insensitive),
    keeping the first-seen literal form and preserving order: all of
    `existing` first, then any `incoming` entries not already present."""
    seen = {link_target(link) for link in existing}
    result = list(existing)
    for link in incoming:
        target = link_target(link)
        if target in seen:
            continue
        seen.add(target)
        result.append(link)
    return result
