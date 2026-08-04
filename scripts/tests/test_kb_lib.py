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
