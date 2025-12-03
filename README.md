# Saturday Book Club

This repository keeps our book-club logistics, reading pipeline, and meeting history in one place.

## Folder Map

- `books/` — track everything we're reading.
  - [`to-read.md`](books/to-read.md) keeps nominations and links.
  - [`in-progress.md`](books/in-progress.md) notes current assignments.
  - [`completed.md`](books/completed.md) stores takeaways when we finish a book.
- `meetings/` — agendas and recaps for sessions.
  Start from [`template.md`](meetings/template.md) and keep dated notes next to it.
- `notes/` — deeper reflections or chapter summaries.
  Use [`templates/book-notes-template.md`](notes/templates/book-notes-template.md) when starting a new note.

### How We Use It

1. Nominate a title by adding it to `books/to-read.md` with a short note.
2. Once the group picks it, move it to `books/in-progress.md` and assign facilitators per session.
3. After finishing, summarize key insights in `books/completed.md` and store any long-form notes under `notes/`.
4. For each gathering, copy `meetings/template.md` into `meetings/YYYY-MM-DD.md`, fill in the agenda, and capture action items.

Keeping these files up to date gives everyone a quick snapshot of what we're reading, what's next, and what we've learned together.

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
- Pin the following folders in the sidebar for quick access:
  - `books/`
  - `notes/`
  - `meetings/`

#### How We Use Obsidian

- All book notes, chapter summaries, and meeting agendas are edited directly in Obsidian.
- Use the built‑in preview mode to read markdown comfortably.
- Use the **Templates plugin**:
  - For meetings, copy the structure from `meetings/template.md`.
  - For book notes, start from `notes/templates/book-notes-template.md`.
- Linking between notes (`[[Book Title]]`) is encouraged to make it easier to navigate what we've discussed.
- All changes sync through GitHub—Obsidian works only as an editor/interface.

This setup keeps the repo readable in GitHub while making note‑taking smoother for everyone.

### Environment Initialization

Set up the tooling before contributing changes:

1. Make sure a recent Python 3 interpreter is available (the repo targets 3.13+).
2. Run `make init` once.
  This installs [uv](https://github.com/astral-sh/uv), creates the virtual environment, adds `pre-commit`, and installs the Git hooks.
3. From then on, use `uv run …` (or `make …` targets) so you reuse the configured environment.

This keeps everyone on the same dependency versions and guarantees the formatting / lint hooks match what CI expects.
