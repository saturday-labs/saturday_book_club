# Knowledge Base

This directory contains our philosophical knowledge system.  
The structure here is intentionally **flat** — all notes live in a single layer without sub‑folders. This keeps linking easy and improves Obsidian graph navigation.

## How to Work With This Folder

- Every file should be an **atomic note** about an author, movement, concept, book, or period.
- Notes should be created **only using templates** from `templates/` to keep metadata consistent across the vault.
- Files should be named clearly (e.g., `kant.md`, `stoicism.md`, `will_to_power.md`) so the graph remains readable.

## Templates

Use the following templates when creating new notes:

### `author.md`

For philosophers and key thinkers.  
Includes metadata, movements, and Dataview tables.

### `movement.md`

For philosophical schools or traditions.  
Captures principles, historical context, key authors, and linked works.

### `book.md`

For philosophical works.  
Summaries, key ideas, quotes, discussion notes, and Dataview references.

### `concept.md`

The core of the system — atomic ideas.  
Contains definitions, explanations, context, criticism, and links to authors/movements/books.

### `period.md`

For historical eras.  
Includes timeframe, intellectual characteristics, and Dataview listings (authors, movements, books, and concepts from this period).

### `country.md`

For countries associated with authors. Minimal frontmatter; surfaces authors via an inverse Dataview query.

## Relationship Schema

**Rule: every relationship is stored on exactly one side.** The other side
gets it through an inverse Dataview query (`WHERE type = "X" AND
contains(field, this.file.name)`) — the same inverse-query pattern
demonstrated by `country.md`'s author listing and `movement.md`'s "Works
Related to This Movement" section.
No relationship is ever hand-maintained on both ends.

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

## Why This Matters

Keeping all notes flat + using standardized templates ensures:

- easy search and navigation  
- consistent metadata for Dataview  
- a clean Obsidian graph  
- predictable linking between ideas, authors, and eras

This directory is the long‑term philosophical memory of our book club — use it to capture insights, connect concepts, and build a living network of understanding.
