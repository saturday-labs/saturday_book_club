# Knowledge Base Schema Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all 40 notes in `knowledge_base/` (plus the 6 templates and the
README) to the single-sourced relationship schema in
`docs/superpowers/specs/2026-08-04-knowledge-base-schema-design.md`, with zero
link data lost or duplicated.

**Architecture:** A small library of pure functions (`scripts/kb_lib.py`)
handles frontmatter I/O and wikilink normalization. A pure transform function
(`scripts/migrate_kb_schema.py::migrate_notes`) takes the whole vault's
frontmatter as an in-memory dict and returns the migrated version — no file
I/O, fully unit-testable. An edge-set extractor
(`scripts/kb_edges.py::extract_edges`) computes a schema-agnostic set of
relationship edges from a vault, used to verify old-vault-edges ==
new-vault-edges before touching real files. Real file I/O (reading the vault,
writing it back, `git mv`) is a thin CLI wrapper around these pure pieces.

**Tech Stack:** Python 3.13 (already the repo's target per `README.md`), run
via `uv run --with pyyaml --with pytest ...` — no `pyproject.toml` needed,
`uv`'s `--with` flag installs ephemeral dependencies per invocation.

## Global Constraints

- Scope is `knowledge_base/**` only — do not touch `books/`, `site/`, or CI
  workflows (spec's "Explicitly out of scope" section).
- Every relationship must end up stored on exactly one side (spec's ownership
  table) — no field may exist on both ends after migration.
- All 40 existing notes are migrated in one pass, not gradually (spec
  decision).
- File naming: `snake_case.md` everywhere; rename the 5 outliers via `git mv`
  so history is preserved.
- Display name: `title` everywhere; drop `name`.
- Drop `author.rating` (unused).
- No data loss: the set of relationship edges implied by the old schema must
  equal the set implied by the new schema (verified mechanically in Task 4,
  not just eyeballed).
- PyYAML's `safe_load`/`safe_dump` do not preserve YAML comments. The only
  place this matters is the `# 1 | 2 | ... | 10` comment on `author.rating`,
  and that field is being deleted anyway, so this is a non-issue — noted here
  so nobody "fixes" it later.

---

### Task 1: `scripts/kb_lib.py` — frontmatter I/O and wikilink helpers

**Files:**

- Create: `scripts/kb_lib.py`
- Test: `scripts/tests/test_kb_lib.py`

**Interfaces:**

- Produces: `read_note(path: Path) -> tuple[dict, str]`,
  `write_note(path: Path, frontmatter: dict, body: str) -> None`,
  `normalize_links(value) -> list[str]`, `link_target(link: str) -> str`,
  `merge_links(existing: list[str], incoming: list[str]) -> list[str]`.
  Later tasks import all five from `kb_lib`.

- [ ] **Step 1: Write the failing tests**

Create `scripts/tests/test_kb_lib.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb_lib import normalize_links, link_target, merge_links, read_note, write_note


def test_normalize_links_none():
    assert normalize_links(None) == []


def test_normalize_links_empty_string():
    assert normalize_links("") == []


def test_normalize_links_plain_string():
    assert normalize_links("[[stephen_hawking]]") == ["[[stephen_hawking]]"]


def test_normalize_links_list_of_strings():
    assert normalize_links(["[[a]]", "[[b]]"]) == ["[[a]]", "[[b]]"]


def test_normalize_links_flattens_nested_list():
    # YAML parses the unquoted `[[stephen_hawking]]` flow scalar as a
    # nested list: [["stephen_hawking"]]. normalize_links must flatten it.
    assert normalize_links([["stephen_hawking"]]) == ["stephen_hawking"]


def test_link_target_bracketed():
    assert link_target("[[Stephen_Hawking]]") == "stephen_hawking"


def test_link_target_bracketed_with_alias():
    assert link_target("[[stephen_hawking|Hawking]]") == "stephen_hawking"


def test_link_target_bare_string():
    # Fallback for the flattened-nested-list case above: no brackets,
    # treat the whole string as the target.
    assert link_target("stephen_hawking") == "stephen_hawking"


def test_merge_links_dedups_by_target_case_insensitive():
    existing = ["[[france]]"]
    incoming = ["[[France]]", "[[germany]]"]
    assert merge_links(existing, incoming) == ["[[france]]", "[[germany]]"]


def test_merge_links_preserves_order_existing_first():
    assert merge_links(["[[b]]"], ["[[a]]", "[[b]]"]) == ["[[b]]", "[[a]]"]


def test_read_note_splits_frontmatter_and_body(tmp_path):
    note = tmp_path / "test_note.md"
    note.write_text(
        "---\ntitle: Test Note\ntype: concept\n---\n\n# Test Note\n\nBody text.\n",
        encoding="utf-8",
    )
    fm, body = read_note(note)
    assert fm == {"title": "Test Note", "type": "concept"}
    assert body == "\n# Test Note\n\nBody text.\n"


def test_write_note_round_trips(tmp_path):
    note = tmp_path / "test_note.md"
    write_note(note, {"title": "Test Note", "type": "concept"}, "\nBody.\n")
    fm, body = read_note(note)
    assert fm == {"title": "Test Note", "type": "concept"}
    assert body == "\nBody.\n"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pyyaml --with pytest pytest scripts/tests/test_kb_lib.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kb_lib'` (the file
doesn't exist yet).

- [ ] **Step 3: Write the implementation**

Create `scripts/kb_lib.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pyyaml --with pytest pytest scripts/tests/test_kb_lib.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/kb_lib.py scripts/tests/test_kb_lib.py
git commit -m "feat: add frontmatter I/O and wikilink helpers for KB migration"
```

---

### Task 2: `scripts/kb_edges.py` — schema-agnostic relationship edge extraction

**Files:**

- Create: `scripts/kb_edges.py`
- Test: `scripts/tests/test_kb_edges.py`

**Interfaces:**

- Consumes: `normalize_links`, `link_target` from `kb_lib` (Task 1).
- Produces: `OLD_FIELD_MAP`, `NEW_FIELD_MAP` (module-level constants — later
  tasks and the Task 4 verification step both import these), `extract_edges(notes: dict[str, dict], field_map: list[tuple]) -> set[tuple]`.

- [ ] **Step 1: Write the failing tests**

Create `scripts/tests/test_kb_edges.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb_edges import OLD_FIELD_MAP, NEW_FIELD_MAP, extract_edges


def test_extract_edges_old_schema_single_sided_field():
    notes = {
        "sartre": {"type": "author", "key_works": ["[[nausea]]"]},
        "nausea": {"type": "book"},
    }
    edges = extract_edges(notes, OLD_FIELD_MAP)
    assert ("author_book", "nausea", "sartre") in edges


def test_extract_edges_old_schema_both_sides_produce_same_edge():
    # author.key_works and book.author both encode author_book in the old
    # schema. If a vault happens to have BOTH sides filled in consistently,
    # extract_edges must not double-count it as two different edges.
    notes = {
        "sartre": {"type": "author", "key_works": ["[[nausea]]"]},
        "nausea": {"type": "book", "author": ["[[sartre]]"]},
    }
    edges = extract_edges(notes, OLD_FIELD_MAP)
    author_book_edges = {e for e in edges if e[0] == "author_book"}
    assert author_book_edges == {("author_book", "nausea", "sartre")}


def test_extract_edges_new_schema_owner_side_only():
    notes = {
        "sartre": {"type": "author"},
        "nausea": {"type": "book", "authors": ["[[sartre]]"]},
    }
    edges = extract_edges(notes, NEW_FIELD_MAP)
    assert edges == {("author_book", "nausea", "sartre")}


def test_extract_edges_ignores_dangling_link():
    notes = {"sartre": {"type": "author", "key_works": ["[[nonexistent_book]]"]}}
    edges = extract_edges(notes, OLD_FIELD_MAP)
    assert edges == set()


def test_extract_edges_ignores_wrong_type_target():
    # concepts field pointing at something that isn't actually a concept
    notes = {
        "sartre": {"type": "author", "concepts": ["[[nausea]]"]},
        "nausea": {"type": "book"},
    }
    edges = extract_edges(notes, OLD_FIELD_MAP)
    assert edges == set()


def test_movement_authors_merges_founders_and_key_authors_in_old_schema():
    notes = {
        "existentialism": {
            "type": "movement",
            "founders": ["[[sartre]]"],
            "key_authors": ["[[camus]]"],
        },
        "sartre": {"type": "author"},
        "camus": {"type": "author"},
    }
    edges = extract_edges(notes, OLD_FIELD_MAP)
    assert ("author_movement", "existentialism", "sartre") in edges
    assert ("author_movement", "camus", "existentialism") in edges
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pyyaml --with pytest pytest scripts/tests/test_kb_edges.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'kb_edges'`.

- [ ] **Step 3: Write the implementation**

Create `scripts/kb_edges.py`:

```python
"""Schema-agnostic relationship edge extraction for the knowledge_base
vault. Used to verify that a schema migration loses and duplicates nothing:
extract_edges(old_vault, OLD_FIELD_MAP) must equal
extract_edges(new_vault, NEW_FIELD_MAP)."""

from kb_lib import link_target, normalize_links

# (source_type, field, target_type, relationship_key)
# relationship_key is shared by both sides of a duplicated relationship so
# extract_edges produces the same edge regardless of which side stores it.
OLD_FIELD_MAP = [
    ("author", "key_works", "book", "author_book"),
    ("book", "author", "author", "author_book"),
    ("author", "concepts", "concept", "author_concept"),
    ("concept", "authors", "author", "author_concept"),
    ("author", "movements", "movement", "author_movement"),
    ("movement", "founders", "author", "author_movement"),
    ("movement", "key_authors", "author", "author_movement"),
    ("author", "period", "period", "author_period"),
    ("period", "major_authors", "author", "author_period"),
    ("author", "country", "country", "author_country"),
    ("book", "concepts", "concept", "book_concept"),
    ("concept", "books", "book", "book_concept"),
    ("book", "movements", "movement", "book_movement"),
    ("movement", "key_works", "book", "book_movement"),
    ("book", "period", "period", "book_period"),
    ("movement", "concepts", "concept", "movement_concept"),
    ("concept", "movements", "movement", "movement_concept"),
    ("movement", "period", "period", "movement_period"),
    ("period", "major_movements", "movement", "movement_period"),
    ("concept", "periods", "period", "concept_period"),
    ("period", "major_concepts", "concept", "concept_period"),
]

NEW_FIELD_MAP = [
    ("book", "authors", "author", "author_book"),
    ("concept", "authors", "author", "author_concept"),
    ("movement", "authors", "author", "author_movement"),
    ("author", "periods", "period", "author_period"),
    ("author", "countries", "country", "author_country"),
    ("book", "concepts", "concept", "book_concept"),
    ("book", "movements", "movement", "book_movement"),
    ("book", "periods", "period", "book_period"),
    ("movement", "concepts", "concept", "movement_concept"),
    ("movement", "periods", "period", "movement_period"),
    ("concept", "periods", "period", "concept_period"),
]


def extract_edges(notes: dict, field_map: list[tuple]) -> set[tuple]:
    """notes: {stem: frontmatter_dict}. Returns a set of
    (relationship_key, note_a, note_b) tuples, note_a < note_b
    alphabetically, so the same edge from either side of a duplicated field
    collapses to one entry. Links to a stem not present in `notes`, or whose
    `type` doesn't match the field map's expected target_type, are ignored."""
    edges: set[tuple] = set()
    for stem, frontmatter in notes.items():
        if not isinstance(frontmatter, dict):
            continue
        for source_type, field, target_type, rel_key in field_map:
            if frontmatter.get("type") != source_type:
                continue
            for link in normalize_links(frontmatter.get(field)):
                target = link_target(link)
                if target not in notes:
                    continue
                if notes[target].get("type") != target_type:
                    continue
                pair = tuple(sorted((stem.lower(), target)))
                edges.add((rel_key, *pair))
    return edges


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from kb_lib import read_note

    if len(sys.argv) != 3 or sys.argv[1] not in ("old", "new"):
        print("Usage: kb_edges.py old|new <knowledge_base_dir>", file=sys.stderr)
        sys.exit(2)

    schema, vault_dir = sys.argv[1], Path(sys.argv[2])
    field_map = OLD_FIELD_MAP if schema == "old" else NEW_FIELD_MAP

    notes = {}
    for path in sorted(vault_dir.glob("*.md")):
        if path.stem.lower() == "readme":
            continue
        fm, _ = read_note(path)
        notes[path.stem.lower()] = fm

    for edge in sorted(extract_edges(notes, field_map)):
        print(",".join(edge))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pyyaml --with pytest pytest scripts/tests/test_kb_edges.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/kb_edges.py scripts/tests/test_kb_edges.py
git commit -m "feat: add relationship edge extraction for KB schema verification"
```

---

### Task 3: `scripts/migrate_kb_schema.py` — the pure migration transform

**Files:**

- Create: `scripts/migrate_kb_schema.py`
- Test: `scripts/tests/test_migrate_kb_schema.py`

**Interfaces:**

- Consumes: `normalize_links`, `link_target`, `merge_links` from `kb_lib`
  (Task 1).
- Produces: `migrate_notes(notes: dict[str, dict]) -> dict[str, dict]` (pure,
  no file I/O — Task 4 and Task 5 both call this). CLI entry point (`if
  __name__ == "__main__"`) is exercised only in Task 4/5, not unit-tested
  here.

**Important ordering property this task must get right:** four fields are
both (a) directly renamed/initialized on their owning note type and (b) a
target of a reverse-merge from some *other* note's losing-side field
(`book.authors`, `movement.authors`, `author.periods`, `movement.periods`).
Both operations must *merge into* the field, never blind-overwrite it —
otherwise whichever one runs second (dict iteration order is insertion
order, i.e. alphabetical by stem given how Task 4/5 build the dict) wins and
silently discards the other's data. The tests below construct the same
input in two different key orders and assert identical output specifically
to catch this class of bug.

- [ ] **Step 1: Write the failing tests**

Create `scripts/tests/test_migrate_kb_schema.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from migrate_kb_schema import migrate_notes


def test_title_replaces_name():
    notes = {"kant": {"type": "author", "name": "Immanuel Kant"}}
    result = migrate_notes(notes)
    assert result["kant"]["title"] == "Immanuel Kant"
    assert "name" not in result["kant"]


def test_rating_dropped():
    notes = {"kant": {"type": "author", "rating": 7}}
    result = migrate_notes(notes)
    assert "rating" not in result["kant"]


def test_author_country_renamed_and_wrapped_in_array():
    notes = {"sartre": {"type": "author", "country": "[[france]]"}}
    result = migrate_notes(notes)
    assert result["sartre"]["countries"] == ["[[france]]"]
    assert "country" not in result["sartre"]


def test_author_key_works_merges_into_book_authors():
    notes = {
        "sartre": {"type": "author", "key_works": ["[[nausea]]"]},
        "nausea": {"type": "book", "author": []},
    }
    result = migrate_notes(notes)
    assert result["nausea"]["authors"] == ["[[sartre]]"]
    assert "key_works" not in result["sartre"]
    assert "author" not in result["nausea"]


def test_book_author_rename_merges_with_reverse_added_author():
    # book.author (owner-side rename) and author.key_works (loser-side
    # reverse-merge) both write into book.authors. Neither may overwrite
    # the other, regardless of which note is processed first.
    notes_a = {
        "nausea": {"type": "book", "author": ["[[camus]]"]},
        "sartre": {"type": "author", "key_works": ["[[nausea]]"]},
    }
    notes_b = {
        "sartre": {"type": "author", "key_works": ["[[nausea]]"]},
        "nausea": {"type": "book", "author": ["[[camus]]"]},
    }
    result_a = migrate_notes(notes_a)
    result_b = migrate_notes(notes_b)
    assert result_a["nausea"]["authors"] == ["[[camus]]", "[[sartre]]"]
    assert result_b["nausea"]["authors"] == ["[[camus]]", "[[sartre]]"]


def test_movement_authors_merges_founders_key_authors_and_reverse_author_link():
    notes = {
        "existentialism": {
            "type": "movement",
            "founders": ["[[sartre]]"],
            "key_authors": ["[[camus]]"],
        },
        "sartre": {"type": "author"},
        "camus": {"type": "author", "movements": ["[[existentialism]]"]},
    }
    result = migrate_notes(notes)
    assert result["existentialism"]["authors"] == ["[[sartre]]", "[[camus]]"]
    assert "founders" not in result["existentialism"]
    assert "key_authors" not in result["existentialism"]
    assert "movements" not in result["camus"]


def test_author_period_reverse_merge_does_not_clobber_own_rename():
    notes = {
        "sartre": {"type": "author", "period": ["[[early_20th_century]]"]},
        "early_20th_century": {
            "type": "period",
            "major_authors": ["[[camus]]"],
        },
        "camus": {"type": "author"},
    }
    result = migrate_notes(notes)
    assert set(result["sartre"]["periods"]) == {"[[early_20th_century]]"}
    assert set(result["camus"]["periods"]) == {"[[early_20th_century]]"}
    assert "major_authors" not in result["early_20th_century"]


def test_concept_and_book_and_movement_forward_fields_untouched():
    notes = {
        "existence_precedes_essence": {
            "type": "concept",
            "authors": ["[[sartre]]"],
            "periods": ["[[early_20th_century]]"],
        }
    }
    result = migrate_notes(notes)
    assert result["existence_precedes_essence"]["authors"] == ["[[sartre]]"]
    assert result["existence_precedes_essence"]["periods"] == [
        "[[early_20th_century]]"
    ]


def test_country_note_unchanged_besides_title():
    notes = {"france": {"type": "country", "name": "France"}}
    result = migrate_notes(notes)
    assert result["france"] == {"type": "country", "title": "France"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pyyaml --with pytest pytest scripts/tests/test_migrate_kb_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'migrate_kb_schema'`.

- [ ] **Step 3: Write the implementation**

Create `scripts/migrate_kb_schema.py`:

```python
"""Migrates knowledge_base/ notes from the old duplicated-relationship
schema to the single-sourced schema in
docs/superpowers/specs/2026-08-04-knowledge-base-schema-design.md.

Pure transform: migrate_notes(). CLI wrapper below does real file I/O and
the 5 git-tracked renames; run it with --dry-run first (see Task 4)."""

from kb_lib import merge_links, normalize_links


def migrate_notes(notes: dict) -> dict:
    """notes: {stem: old_frontmatter_dict}. Returns {stem: new_frontmatter_dict}.
    Does not mutate the input. Only touches the fields covered by the
    ownership table in the design spec; unrelated attribute fields
    (birth, death, year, status, origin, start, end, tags, created,
    updated, type) pass through unchanged."""
    result = {stem: dict(fm) for stem, fm in notes.items()}

    def get_links(stem: str, field: str) -> list[str]:
        return normalize_links(result[stem].get(field))

    def targets_of_type(stem: str, field: str, wanted_type: str) -> list[str]:
        out = []
        for link in get_links(stem, field):
            from kb_lib import link_target

            target = link_target(link)
            if target in result and result[target].get("type") == wanted_type:
                out.append(target)
        return out

    def add_reverse(owner_stem: str, owner_field: str, note_stem: str) -> None:
        link = f"[[{note_stem}]]"
        current = get_links(owner_stem, owner_field)
        result[owner_stem][owner_field] = merge_links(current, [link])

    for stem in list(result.keys()):
        fm = result[stem]
        note_type = fm.get("type")

        if "name" in fm:
            fm.setdefault("title", fm.pop("name"))

        if note_type == "author":
            fm.pop("rating", None)

            for book_stem in targets_of_type(stem, "key_works", "book"):
                add_reverse(book_stem, "authors", stem)
            fm.pop("key_works", None)

            for concept_stem in targets_of_type(stem, "concepts", "concept"):
                add_reverse(concept_stem, "authors", stem)
            fm.pop("concepts", None)

            for movement_stem in targets_of_type(stem, "movements", "movement"):
                add_reverse(movement_stem, "authors", stem)
            fm.pop("movements", None)

            fm["periods"] = merge_links(get_links(stem, "periods"), get_links(stem, "period"))
            fm.pop("period", None)

            fm["countries"] = get_links(stem, "country")
            fm.pop("country", None)

        elif note_type == "book":
            fm["authors"] = merge_links(get_links(stem, "authors"), get_links(stem, "author"))
            fm.pop("author", None)

            fm["periods"] = get_links(stem, "period")
            fm.pop("period", None)

        elif note_type == "concept":
            for book_stem in targets_of_type(stem, "books", "book"):
                add_reverse(book_stem, "concepts", stem)
            fm.pop("books", None)

            for movement_stem in targets_of_type(stem, "movements", "movement"):
                add_reverse(movement_stem, "concepts", stem)
            fm.pop("movements", None)

        elif note_type == "movement":
            founders = get_links(stem, "founders")
            key_authors = get_links(stem, "key_authors")
            fm["authors"] = merge_links(
                get_links(stem, "authors"), merge_links(founders, key_authors)
            )
            fm.pop("founders", None)
            fm.pop("key_authors", None)

            for book_stem in targets_of_type(stem, "key_works", "book"):
                add_reverse(book_stem, "movements", stem)
            fm.pop("key_works", None)

            fm["periods"] = merge_links(get_links(stem, "periods"), get_links(stem, "period"))
            fm.pop("period", None)

        elif note_type == "period":
            for author_stem in targets_of_type(stem, "major_authors", "author"):
                add_reverse(author_stem, "periods", stem)
            fm.pop("major_authors", None)

            for movement_stem in targets_of_type(stem, "major_movements", "movement"):
                add_reverse(movement_stem, "periods", stem)
            fm.pop("major_movements", None)

            for concept_stem in targets_of_type(stem, "major_concepts", "concept"):
                add_reverse(concept_stem, "periods", stem)
            fm.pop("major_concepts", None)

    return result


if __name__ == "__main__":
    # CLI wrapper -- exercised in Task 4 (dry run) and Task 5 (real run).
    import sys
    from pathlib import Path

    from kb_lib import read_note, write_note

    if len(sys.argv) != 2:
        print("Usage: migrate_kb_schema.py <knowledge_base_dir>", file=sys.stderr)
        sys.exit(2)

    vault_dir = Path(sys.argv[1])
    note_paths = {
        path.stem.lower(): path
        for path in vault_dir.glob("*.md")
        if path.stem.lower() != "readme"
    }
    notes = {stem: read_note(path)[0] for stem, path in note_paths.items()}
    bodies = {stem: read_note(path)[1] for stem, path in note_paths.items()}

    migrated = migrate_notes(notes)

    for stem, path in note_paths.items():
        write_note(path, migrated[stem], bodies[stem])

    print(f"Migrated {len(note_paths)} notes in {vault_dir}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pyyaml --with pytest pytest scripts/tests/test_migrate_kb_schema.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_kb_schema.py scripts/tests/test_migrate_kb_schema.py
git commit -m "feat: add pure KB schema migration transform"
```

---

### Task 4: Dry-run against a copy of the vault and verify zero edge loss

**Files:**

- Modify: none (this task only reads/writes a temp copy)
- No new source files — this is a verification gate using Tasks 1-3's scripts

**Interfaces:**

- Consumes: `extract_edges`, `OLD_FIELD_MAP`, `NEW_FIELD_MAP` from
  `kb_edges.py`; the `migrate_kb_schema.py` CLI.

- [ ] **Step 1: Copy the vault to a temp directory**

```bash
rm -rf /tmp/kb_migration_dry_run
cp -r knowledge_base /tmp/kb_migration_dry_run
rm -rf /tmp/kb_migration_dry_run/templates
```

(`templates/` contains Templater placeholders like `<% tp.file.title %>`
which are not valid YAML — excluded from this dry run; templates are
rewritten by hand in Task 5, not migrated by this script.)

- [ ] **Step 2: Extract the OLD-schema edge set from the real vault**

```bash
uv run --with pyyaml python scripts/kb_edges.py old knowledge_base > /tmp/edges_old.txt
wc -l /tmp/edges_old.txt
```

Expected: some non-zero line count (one line per relationship edge found in
the real vault today).

- [ ] **Step 3: Run the migration against the copy**

```bash
uv run --with pyyaml python scripts/migrate_kb_schema.py /tmp/kb_migration_dry_run
```

Expected output: `Migrated 39 notes in /tmp/kb_migration_dry_run` (39 = 40
real notes minus `README.md`, which `migrate_kb_schema.py` skips).

- [ ] **Step 4: Extract the NEW-schema edge set from the migrated copy**

```bash
uv run --with pyyaml python scripts/kb_edges.py new /tmp/kb_migration_dry_run > /tmp/edges_new.txt
diff <(sort /tmp/edges_old.txt) <(sort /tmp/edges_new.txt)
```

Expected: **no output** (empty diff). Empty diff means the migration lost
and duplicated exactly zero relationship edges.

If the diff is non-empty: do not proceed to Task 5. Read the specific
mismatched edge lines, find which note(s) they involve, and check whether
`migrate_notes` (Task 3) is missing a case for that note's exact field
combination — most likely cause is a real note using a field shape the
Task 3 unit tests didn't cover (e.g. a scalar where the tests assumed a
list). Add a regression test reproducing it, fix `migrate_notes`, and
re-run Task 4 from Step 1.

- [ ] **Step 5: No commit for this task**

This task only ran verification against temp files — nothing in the repo
changed. Proceed to Task 5 only once Step 4's diff is empty.

---

### Task 5: Apply the migration for real, rewrite templates and README, verify the site still builds

**Files:**

- Modify (via script): all `knowledge_base/*.md` notes except `README.md`
- Rename: `knowledge_base/France.md` → `knowledge_base/france.md`,
  `Germany.md` → `germany.md`, `Humanism.md` → `humanism.md`,
  `Existentialism.md` → `existentialism.md`, `Nausea.md` → `nausea.md`
- Modify: `knowledge_base/templates/author.md`,
  `knowledge_base/templates/book.md`, `knowledge_base/templates/concept.md`,
  `knowledge_base/templates/country.md`,
  `knowledge_base/templates/movement.md`,
  `knowledge_base/templates/period.md`
- Modify: `knowledge_base/README.md`

- [ ] **Step 1: Rename the 5 outlier files with git mv**

```bash
cd knowledge_base
git mv France.md france.md
git mv Germany.md germany.md
git mv Humanism.md humanism.md
git mv Existentialism.md existentialism.md
git mv Nausea.md nausea.md
cd ..
```

- [ ] **Step 2: Run the migration for real**

```bash
uv run --with pyyaml python scripts/migrate_kb_schema.py knowledge_base
```

Expected output: `Migrated 39 notes in knowledge_base`.

- [ ] **Step 3: Re-verify zero edge loss against the real (now-migrated) vault**

```bash
uv run --with pyyaml python scripts/kb_edges.py new knowledge_base > /tmp/edges_new_real.txt
diff <(sort /tmp/edges_old.txt) <(sort /tmp/edges_new_real.txt)
```

Expected: no output (same check as Task 4, now against the real vault
instead of the temp copy — confirms `git mv` plus the real run produced the
identical result the dry run predicted).

- [ ] **Step 4: Fix the dead "Related Concepts" query — remove it from movement notes**

The old `movement.md` template (and every real movement note, since new
notes are created from it) ships this block, which always returns empty
because it checks `type = "movement"` instead of `type = "concept"`:

````markdown
## Related Concepts

```dataview
TABLE name AS "Movement", period AS "Period"
FROM "knowledge_base"
WHERE type = "movement"
AND contains(concepts, this.file.name)
SORT name ASC
```
````

Run this to remove that exact block from every real movement-type note's
body (post-migration, so `type` is still `movement` — this field was never
renamed):

````bash
uv run --with pyyaml python - <<'PYEOF'
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from kb_lib import read_note, write_note

DEAD_BLOCK = '''## Related Concepts

```dataview
TABLE name AS "Movement", period AS "Period"
FROM "knowledge_base"
WHERE type = "movement"
AND contains(concepts, this.file.name)
SORT name ASC
```

'''

vault = Path("knowledge_base")
for path in sorted(vault.glob("*.md")):
    fm, body = read_note(path)
    if fm.get("type") != "movement":
        continue
    if DEAD_BLOCK in body:
        write_note(path, fm, body.replace(DEAD_BLOCK, ""))
        print(f"removed dead block from {path}")
PYEOF
````

Expected: prints one `removed dead block from ...` line per movement note
that had it (matches the count found in Task 1's exploration: France,
existentialism, critical_theory, Humanism, and any other movement-type note
with the block — verify the count looks right by eye, there is no
independent oracle for this count).

- [ ] **Step 5: Add the corrected inverse query to concept notes**

Add a "Related Movements" section with the corrected query (uses the new
field names: `title` instead of `name`, `periods` instead of `period`) to
every concept-type note's body, right before the end of the file, only if
it doesn't already have one:

````bash
uv run --with pyyaml python - <<'PYEOF'
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from kb_lib import read_note, write_note

NEW_BLOCK = '''
## Related Movements

```dataview
TABLE title AS "Movement", periods AS "Period"
FROM "knowledge_base"
WHERE type = "movement"
AND contains(concepts, this.file.name)
SORT title ASC
```
'''

vault = Path("knowledge_base")
for path in sorted(vault.glob("*.md")):
    fm, body = read_note(path)
    if fm.get("type") != "concept":
        continue
    if "## Related Movements" in body:
        continue
    write_note(path, fm, body.rstrip("\n") + "\n" + NEW_BLOCK)
    print(f"added Related Movements block to {path}")
PYEOF
````

- [ ] **Step 6: Rewrite the 6 templates**

Replace `knowledge_base/templates/author.md` frontmatter block with:

```yaml
---
title: <% tp.file.title %>
periods: []
countries: []
nationality: ""
birth: null
death: null
type: author
tags: ["author"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---
```

Replace `knowledge_base/templates/book.md` frontmatter block with:

```yaml
---
title: <% tp.file.title %>
authors: []
year:
concepts: []
movements: []
periods: []
status: to-read
type: book
tags:
  - book
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---
```

Replace `knowledge_base/templates/concept.md` frontmatter block with:

```yaml
---
title: <% tp.file.title %>
authors: []
periods: []
type: concept
tags: ["concept"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---
```

Append this section at the end of `knowledge_base/templates/concept.md`
(after "## Practical Use / Real-Life Reflection"), matching Step 5's new
block exactly:

````markdown

## Related Movements

```dataview
TABLE title AS "Movement", periods AS "Period"
FROM "knowledge_base"
WHERE type = "movement"
AND contains(concepts, this.file.name)
SORT title ASC
```
````

Replace `knowledge_base/templates/country.md`'s dataview block (frontmatter
is already minimal and correct, no change needed there) so it uses the new
field names:

````markdown
```dataview
TABLE title AS "Author", periods AS "Period"
FROM "knowledge_base"
WHERE type = "author"
AND contains(countries, this.file.name)
SORT title ASC
```
````

Replace `knowledge_base/templates/movement.md` frontmatter block with:

```yaml
---
title: <% tp.file.title %>
periods: []
origin: ""
concepts: []
authors: []
type: movement
tags: ["movement"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---
```

Delete the "## Related Concepts" section entirely from
`knowledge_base/templates/movement.md` (it moved to `concept.md` above).
Keep "## Works Related to This Movement" as-is except its query's `FROM`
clause and field names already match the new schema (`movements`, `author`
column reads from `book.authors` which Dataview surfaces as `authors` — update
the column list to `authors AS "Author"`):

````markdown
## Works Related to This Movement

```dataview
TABLE title AS "Title", authors AS "Author", year AS "Year"
FROM "knowledge_base"
WHERE type = "book"
AND contains(movements, this.file.name)
SORT year ASC
```
````

Replace `knowledge_base/templates/period.md` frontmatter block with:

```yaml
---
title: <% tp.file.title %>
start: null
end: null
type: period
tags: ["period"]
created: <% tp.file.creation_date("DD/MM/yyyy HH:mm:ss") %>
updated: <% tp.file.last_modified_date("DD/MM/yyyy HH:mm:ss") %>
---
```

- [ ] **Step 7: Rewrite `knowledge_base/README.md`**

Replace the "How to Work With This Folder" file-naming bullet's example from
`will-to-power.md` to `will_to_power.md`. Add a new "## Relationship Schema"
section right after "## Templates", containing the ownership table from the
spec (copy the table from
`docs/superpowers/specs/2026-08-04-knowledge-base-schema-design.md`'s
"Relationship schema: single-sourcing" section verbatim, since that table
*is* the documentation this section exists to provide).

- [ ] **Step 8: Verify the site still builds cleanly**

```bash
cd site
npx quartz build 2>&1 | tail -20
```

Expected: `Done processing 39 files` (was 36 before this migration — the 5
renamed files were already counted; no note was added or removed, so if the
count differs from the pre-migration build, a note was lost — stop and
investigate rather than proceeding). No `Failed to process markdown` or
`Failed to process html` error lines.

- [ ] **Step 9: grep for leftover old field names across the whole vault**

```bash
grep -rn "^name:\|^period:\|^country:\|^key_works:\|^founders:\|^key_authors:\|^major_authors:\|^major_movements:\|^major_concepts:\|^rating:" knowledge_base/*.md
```

Expected: no output. Any match means a note the migration script missed
(most likely a file with a frontmatter shape the script's `read_note` choked
on silently — it shouldn't fail silently, but re-check by hand if this
grep finds anything).

- [ ] **Step 10: Commit**

```bash
git add knowledge_base/
git commit -m "feat: migrate knowledge_base to single-sourced relationship schema

Renames the 5 CapitalizedWords.md outliers to snake_case, unifies
name/title into title everywhere, and single-sources every
relationship per docs/superpowers/specs/2026-08-04-knowledge-base-schema-design.md.
Also fixes movement.md's dead 'Related Concepts' Dataview query
(checked type = movement instead of type = concept) by moving the
corrected version to concept.md."
```

---

## Self-Review Notes

- **Spec coverage:** naming convention (Task 5 Step 1 + README), title/name
  unification (Task 3), all 11 relationship ownership rules (Task 3, one
  `elif` branch per note type), rating drop (Task 3), migration performed on
  all 40 notes at once (Task 5 Step 2), templates rewritten (Task 5 Step 6),
  README rewritten (Task 5 Step 7), zero-data-loss verification (Task 4 +
  Task 5 Step 3) — every spec section has a task.
- **Beyond the literal spec text:** the spec's "Migration" section describes
  rewriting the dead-query fix only for the *templates* (Task 5 Step 6). This
  plan additionally patches the *existing* movement/concept notes' bodies
  (Task 5 Steps 4-5), since otherwise the 40-note migration would leave every
  current movement note carrying a permanently-broken query. Flagged here in
  case that's not wanted — skip Steps 4-5 to match the spec exactly.
- **Type/name consistency check:** `migrate_notes` (Task 3) and
  `extract_edges`'s `NEW_FIELD_MAP` (Task 2) were cross-checked field-by-field
  against the spec's ownership table — both agree on which type owns which
  field name.
