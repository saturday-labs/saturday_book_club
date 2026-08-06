# Knowledge base schema redesign

**Date:** 2026-08-04
**Scope:** `knowledge_base/**` only — file naming, frontmatter schema, the six note
templates, and `knowledge_base/README.md`. Out of scope: `books/board.md`,
`books/backlog.md`, `site/` (Quartz, dataview-lite), CI workflows. Those are
separate initiatives.

## Problem

The vault has 40 notes across 6 types (author, book, concept, country,
movement, period), each with its own template under `knowledge_base/templates/`.
Three concrete problems, found by reading all six templates and cross-checking
against the 40 real notes:

1. **File naming is inconsistent.** `knowledge_base/README.md` documents
   lowercase names (its own example uses hyphens: `will-to-power.md`) but 34 of
   39 real notes use `snake_case`, and 5 use `CapitalizedWords.md`
   (`France.md`, `Germany.md`, `Humanism.md`, `Existentialism.md`,
   `Nausea.md`).

2. **`title` vs `name` is split arbitrarily.** `book.md` and `concept.md` use
   `title`; `author.md`, `movement.md`, `period.md`, `country.md` use `name`.
   Quartz's frontmatter parser (`note-properties` plugin) auto-fills `title =
   file.stem` whenever `title` is absent, so the four `name`-based types end up
   with a `title` that's just the raw filename, while their real display name
   lives in a second, undocumented field.

3. **Every relationship field is duplicated on both ends, with inconsistent
   names, and one duplicate has drifted into a bug.** Example:
   `book.author` and `author.key_works` both encode the book↔author
   relationship — two places to keep in sync, no enforcement. Naming is
   inconsistent across types: `book.period` (singular) vs `concept.periods`
   (plural) vs `period.major_authors` (prefixed) all refer to variations of
   the same kind of link. One of these duplicates has already drifted into a
   bug: `movement.md`'s "Related Concepts" Dataview block queries
   `WHERE type = "movement" AND contains(concepts, this.file.name)` — it's
   looking for *other movements*, when the query only makes sense on a
   *concept* page (movements whose `concepts` list contains this concept).
   It has always returned empty.

`country.md` doesn't have this problem — it stores nothing itself and queries
authors inversely (`WHERE type = "author" AND country.file.name =
this.file.name`). That's the pattern the rest of the schema should follow.

## Naming convention

All vault files: `snake_case.md` (lowercase, `_` word separator).

Migrate the 5 outliers with `git mv` (preserves history):

| From | To |
| --- | --- |
| `France.md` | `france.md` |
| `Germany.md` | `germany.md` |
| `Humanism.md` | `humanism.md` |
| `Existentialism.md` | `existentialism.md` |
| `Nausea.md` | `nausea.md` |

Update `knowledge_base/README.md`'s own example from `will-to-power.md`
(hyphenated) to `will_to_power.md` (underscored) so the doc matches reality.

## Display name: `title` only

Drop `name` everywhere. All six types use `title` as the single display-name
field. `author.md`, `movement.md`, `period.md`, `country.md` gain `title:
<% tp.file.title %>` in place of `name: <% tp.file.title %>`; their existing
notes' `name` values move to `title`.

## Relationship schema: single-sourcing

**Rule: every relationship is stored on exactly one side.** The other side
gets it through an inverse Dataview query (`WHERE type = "X" AND
contains(field, this.file.name)`) — the same pattern `country.md` and
`book.movements` → "Works Related to This Movement" already use correctly.
No relationship is ever hand-maintained on both ends.

Ownership, chosen by which note you'd naturally be looking at when the fact
is first recorded (e.g. you know a book's author when you catalog the book,
so `book` owns that link, not `author`):

| Relationship | Owner | Field (on owner) | Dropped from other side |
| --- | --- | --- | --- |
| author ↔ book | **book** | `authors[]` | `author.key_works[]` |
| author ↔ concept | **concept** | `authors[]` (unchanged) | `author.concepts[]` |
| author ↔ movement | **movement** | `authors[]` (merges `founders`+`key_authors`) | `author.movements[]` |
| author ↔ period | **author** | `periods[]` | `period.major_authors[]` |
| author ↔ country | **author** | `countries[]` (was singular `country`) | — (country already stored nothing) |
| book ↔ concept | **book** | `concepts[]` (unchanged) | `concept.books[]` |
| book ↔ movement | **book** | `movements[]` (unchanged) | `movement.key_works[]` |
| book ↔ period | **book** | `periods[]` (was singular `period`) | — |
| movement ↔ concept | **movement** | `concepts[]` (unchanged) | `concept.movements[]` |
| movement ↔ period | **movement** | `periods[]` (was singular `period`) | `period.major_movements[]` |
| concept ↔ period | **concept** | `periods[]` (unchanged) | `period.major_concepts[]` |

Net effect per type:

- **book** — owns `authors[]`, `concepts[]`, `movements[]`, `periods[]`. Book
  notes are the relational hub: cataloging a book is when you know all four
  facets at once.
- **concept** — owns `authors[]`, `periods[]`. Drops `books[]`, `movements[]`.
- **movement** — owns `authors[]` (merged from `founders[]` + `key_authors[]`),
  `concepts[]`, `periods[]`. Drops `founders[]`, `key_authors[]`, `key_works[]`.
  Who specifically *founded* vs. was merely a *key figure* becomes prose in
  the note body (narrative, not something queried), not two overlapping
  frontmatter arrays.
- **author** — owns `countries[]`, `periods[]`. Drops `concepts[]`,
  `movements[]`, `key_works[]`, singular `country`.
- **period** — owns nothing; pure label type, same shape as `country.md`
  today.
- **country** — owns nothing (unchanged).

`movement.md`'s buggy "Related Concepts" block is deleted from `movement.md`
and replaced by a correct block added to `concept.md`'s template: "Movements
featuring this concept" (`WHERE type = "movement" AND contains(concepts,
this.file.name)` — now correct, because it runs on a concept page).

Non-relationship attribute fields are unaffected by single-sourcing and stay
put: `author.birth`, `author.death`, `author.nationality`, `book.year`,
`book.status`, `movement.origin`, `period.start`, `period.end`.

`author.rating` (1–10, unused anywhere in the site or elsewhere) is dropped as
dead weight.

## Migration

A one-off script, `scripts/migrate_kb_schema.py` (Python, consistent with the
repo's existing `uv`-based tooling), performs the full cutover in one pass —
all 40 existing notes move to the new schema immediately, not gradually:

1. `git mv` the 5 `CapitalizedWords.md` files to `snake_case.md`.
2. For every note: rename/merge/drop frontmatter fields per the ownership
   table above; rename `name` → `title` where applicable.
3. Rewrite the 6 templates under `knowledge_base/templates/` with the new
   field list and corrected Dataview blocks (delete the buggy block from
   `movement.md`; add the corrected inverse block to `concept.md`; add/adjust
   inverse-query blocks to `author.md`, `period.md`, `book.md`, and
   `movement.md` so each note surfaces what points at it, not just what it
   points to).
4. Rewrite `knowledge_base/README.md`: naming convention example, and the
   ownership table as the documented schema reference.

The script is kept in the repo after running it (not deleted), as a record of
how the migration was done and a starting point if a similar schema change is
needed later.

## Explicitly out of scope

- Anything under `books/` (`board.md`, `backlog.md`) — a separate structure
  problem (three sources of truth for reading status), tracked as its own
  initiative.
- `site/` — Quartz config, `dataview-lite` plugin, page rendering. The schema
  change here is compatible with `dataview-lite`'s existing query engine (no
  new query shapes introduced), but wiring the site's `note-properties`
  `includedProperties` to visibly render the new owned relationship fields on
  each page is a site-side follow-up, not part of this spec.
- CI/automation (e.g. a lint check that catches future schema drift) — a
  natural next step once this schema exists, but not built here.
