"""Migrates knowledge_base/ notes from the old duplicated-relationship
schema to the single-sourced schema in
docs/superpowers/specs/2026-08-04-knowledge-base-schema-design.md.

Pure transform: migrate_notes(). CLI wrapper below does real file I/O and
the 5 git-tracked renames; run it with --dry-run first (see Task 4)."""

from kb_lib import link_target, merge_links, normalize_links


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

            fm["periods"] = merge_links(get_links(stem, "period"), get_links(stem, "periods"))
            fm.pop("period", None)

            fm["countries"] = get_links(stem, "country")
            fm.pop("country", None)

        elif note_type == "book":
            fm["authors"] = merge_links(get_links(stem, "author"), get_links(stem, "authors"))
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
                merge_links(founders, key_authors), get_links(stem, "authors")
            )
            fm.pop("founders", None)
            fm.pop("key_authors", None)

            for book_stem in targets_of_type(stem, "key_works", "book"):
                add_reverse(book_stem, "movements", stem)
            fm.pop("key_works", None)

            fm["periods"] = merge_links(get_links(stem, "period"), get_links(stem, "periods"))
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
