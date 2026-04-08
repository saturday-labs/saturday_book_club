# Contributing Guide

This guide explains how to name branches, write commit messages, and format PR titles in this repository.
Rules below are aligned with current GitHub Actions checks in `.github/workflows`.

## What CI Validates Today

| Check | Workflow | What is validated |
| --- | --- | --- |
| Branch name | `.github/workflows/branch-name-check.yml` | Branch must match `^(feat|fix|chore|docs|refactor)/[a-z0-9._-]+$` |
| Commit messages | `.github/workflows/commitlint.yml` + `commitlint.config.js` | Conventional commit header rules and allowed commit types |

## Branch Naming

Required pattern:

```text
^(feat|fix|chore|docs|refactor)/[a-z0-9._-]+$
```

Allowed prefixes:

- `feat`
- `fix`
- `chore`
- `docs`
- `refactor`

Examples:

- Valid: `feat/add-new-reading-list`
- Valid: `fix/book-parser-v2`
- Valid: `docs/readme_update`
- Invalid: `feature/add-reading-list` (unsupported prefix)
- Invalid: `feat/AddReadingList` (uppercase letters in suffix)
- Invalid: `feat/add/reading/list` (extra `/` in suffix)

## Commit Messages

Use Conventional Commits style:

```text
<type>(<scope>): <subject>
```

`<scope>` is optional.

Allowed `type` values (from `commitlint.config.js`):

- `build`
- `chore`
- `ci`
- `docs`
- `feat`
- `fix`
- `perf`
- `refactor`
- `revert`
- `style`
- `test`

Additional enforced rules:

- Type must be lower-case.
- Subject must not be empty.
- Subject must not end with `.`.
- Full header length must be `<= 150` characters.

Examples:

- Valid: `feat(books): add queue for next month`
- Valid: `fix: handle empty backlog row`
- Valid: `docs(readme): clarify local setup`
- Invalid: `Feat: add queue` (type case is invalid)
- Invalid: `feature: add queue` (type is not allowed)
- Invalid: `fix:` (empty subject)
- Invalid: `fix: handle empty backlog.` (subject ends with a dot)

## PR Titles

There is currently no dedicated GitHub Action that validates PR title format.
To keep review and release flow consistent, use the same Conventional Commits style for PR titles:

```text
<type>(<scope>): <subject>
```

Examples:

- `feat(books): add april nominations`
- `fix(ci): correct commitlint range`
- `docs: update contribution rules`

## Quick Checklist Before Opening a PR

1. Branch name matches `^(feat|fix|chore|docs|refactor)/[a-z0-9._-]+$`.
2. Every commit in the PR follows commitlint rules.
3. PR title follows Conventional Commits format.
