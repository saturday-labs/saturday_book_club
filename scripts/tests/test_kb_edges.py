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
