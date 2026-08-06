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
