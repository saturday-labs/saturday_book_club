# Saturday Book Club

This repository keeps our book-club logistics, reading pipeline, and meeting history in one place.

## Environment Initialization

Set up the tooling before contributing changes:

1. Make sure a recent Python 3 interpreter is available (the repo targets 3.13+).
2. Run `make init` once.
  This installs [uv](https://github.com/astral-sh/uv), creates the virtual environment, adds `pre-commit`, and installs the Git hooks.
3. From then on, use `uv run …` (or `make …` targets) so you reuse the configured environment.

This keeps everyone on the same dependency versions and guarantees the formatting / lint hooks match what CI expects.

## Folder Map

- `books/` — track everything we're reading via `board.md` and `backlog.md`.
- `knowledge_base/` — our structured philosophical knowledge base built as a flat Obsidian vault.
  See [knowledge_base/README.md](knowledge_base/README.md) for details on how to create and organize notes.

### How We Use It

1. **Nominate books** by adding them to `books/backlog.md` with a short note about why they interest you.
2. **Track reading progress** in `books/board.md` — our Kanban board that shows what we're planning, currently reading, and have completed.
3. **Build knowledge** in the `knowledge_base/` using templates for authors, books, concepts, movements, and periods.
  This creates a connected network of philosophical ideas that grows with each book we read.

Keeping `board.md` and the knowledge base updated gives everyone a quick snapshot of our reading journey and the insights we've gathered together.

### Obsidian

To keep all book notes synchronized and easy to browse, we use Obsidian as our primary knowledge workspace.

#### Installation

1. Download Obsidian from https://obsidian.md.
2. Install it using the default options for your OS.
3. Open Obsidian and choose **Open folder as vault**.
4. Select the root of this repository so all notes, templates, and meeting files are directly available.

#### Recommended Setup

- Enable the core plugins:
  - **Daily Notes** (optional but helpful for quick reflections)
  - **Templates**
  - **File Explorer**
  - **Backlinks**
- Pin the following folders in the sidebar for quick access

#### How We Use Obsidian

- All book notes, chapter, summaries etc. are edited directly in Obsidian.
- Use the built‑in preview mode to read markdown comfortably.
- Use the [**Templater plugin**](https://silentvoid13.github.io/Templater/introduction.html)
- Linking between notes (`[[Book Title]]`) is encouraged to make it easier to navigate what we've discussed.
- All changes sync through GitHub—Obsidian works only as an editor/interface.

This setup keeps the repo readable in GitHub while making note‑taking smoother for everyone.
