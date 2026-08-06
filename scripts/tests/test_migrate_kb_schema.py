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


# --- Additional ordering-regression tests -----------------------------------
#
# test_book_author_rename_merges_with_reverse_added_author (above) is the only
# one of the brief's 9 tests that both (a) uses two different dict key
# orderings and (b) asserts exact list equality (not set equality) on a
# dual-owned field. That combination is exactly what's needed to catch a
# regression of the merge_links-argument-order bug fixed in this file (own
# field must be merge_links's base argument, accumulated reverse-merge value
# must be the incoming argument -- swapping them makes output order depend on
# note-processing order, even though no data is lost either way). The other
# three dual-owned fields (movement.authors, author.periods,
# movement.periods) weren't covered by an equivalent test. These three fill
# that gap, mirroring the book/author test's structure exactly.


def test_movement_authors_rename_merges_with_reverse_added_author_both_orders():
    # movement.authors (owner-side merge of founders+key_authors) and
    # author.movements (loser-side reverse-merge) both write into
    # movement.authors. Neither may overwrite the other, regardless of which
    # note is processed first.
    notes_a = {
        "existentialism": {"type": "movement", "founders": ["[[sartre]]"]},
        "camus": {"type": "author", "movements": ["[[existentialism]]"]},
    }
    notes_b = {
        "camus": {"type": "author", "movements": ["[[existentialism]]"]},
        "existentialism": {"type": "movement", "founders": ["[[sartre]]"]},
    }
    result_a = migrate_notes(notes_a)
    result_b = migrate_notes(notes_b)
    assert result_a["existentialism"]["authors"] == ["[[sartre]]", "[[camus]]"]
    assert result_b["existentialism"]["authors"] == ["[[sartre]]", "[[camus]]"]


def test_author_periods_rename_merges_with_reverse_added_period_both_orders():
    # author.periods (owner-side rename of period) and period.major_authors
    # (loser-side reverse-merge, from a *different* period note) both write
    # into author.periods. Neither may overwrite the other, regardless of
    # which note is processed first.
    notes_a = {
        "sartre": {"type": "author", "period": ["[[early_20th_century]]"]},
        "renaissance": {"type": "period", "major_authors": ["[[sartre]]"]},
    }
    notes_b = {
        "renaissance": {"type": "period", "major_authors": ["[[sartre]]"]},
        "sartre": {"type": "author", "period": ["[[early_20th_century]]"]},
    }
    result_a = migrate_notes(notes_a)
    result_b = migrate_notes(notes_b)
    assert result_a["sartre"]["periods"] == ["[[early_20th_century]]", "[[renaissance]]"]
    assert result_b["sartre"]["periods"] == ["[[early_20th_century]]", "[[renaissance]]"]


def test_movement_periods_rename_merges_with_reverse_added_period_both_orders():
    # movement.periods (owner-side rename of period) and
    # period.major_movements (loser-side reverse-merge, from a *different*
    # period note) both write into movement.periods. Neither may overwrite
    # the other, regardless of which note is processed first.
    notes_a = {
        "existentialism": {"type": "movement", "period": ["[[early_20th_century]]"]},
        "renaissance": {"type": "period", "major_movements": ["[[existentialism]]"]},
    }
    notes_b = {
        "renaissance": {"type": "period", "major_movements": ["[[existentialism]]"]},
        "existentialism": {"type": "movement", "period": ["[[early_20th_century]]"]},
    }
    result_a = migrate_notes(notes_a)
    result_b = migrate_notes(notes_b)
    assert result_a["existentialism"]["periods"] == ["[[early_20th_century]]", "[[renaissance]]"]
    assert result_b["existentialism"]["periods"] == ["[[early_20th_century]]", "[[renaissance]]"]
