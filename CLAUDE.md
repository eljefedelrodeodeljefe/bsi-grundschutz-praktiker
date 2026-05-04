# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Project:** `bsi-grundschutz-praktiker` — terminal Prüfungstrainer for the BSI IT-Grundschutz Praktiker certification.

## Commands

```bash
just install   # uv sync – install deps into .venv
just scrape    # fetch questions from bsi.bund.de → data/questions.json
just quiz      # run the terminal quiz (default: just)
just all       # scrape then quiz
```

Run scripts directly with `uv run python scraper.py` / `uv run python quiz.py`.

## Architecture

Two standalone scripts; no shared modules.

**`scraper.py` → `data/questions.json`**

1. For each entry in `LESSONS`, fetches the lesson index page (`Lektion_X_node.html`) and scans all `<a>` tags to find the "Fragen" and "Lösungen" sub-page URLs dynamically.
2. Fetches only the **Lösungen** page (it contains both questions and correct-answer markers).
3. Parses it by finding `<h2–h4>` headings matching `"Frage \d+"`, then walking next siblings to collect the question `<p>` and answer `<ol>`. Correct answers are identified by `[richtig]` in the `<li>` text.
4. `clean_text()` handles a BSI-specific artifact: compound words like `IT-Grundschutz-Check` are split across inline tags, producing spurious spaces around hyphens.
5. BSI `href` values are root-relative without a leading `/` (e.g. `DE/Themen/...`), so URLs are resolved with `urljoin(BASE_URL + "/", href)` — not against the page URL.

Output schema (`data/questions.json`):
```json
{
  "Sicherheitsmanagement": {
    "lesson": 2,
    "lesson_url": "https://www.bsi.bund.de/...",
    "test_url":   "https://www.bsi.bund.de/...",
    "loesungen_url": "https://www.bsi.bund.de/...",
    "questions": [
      { "number": 1, "question": "...", "answers": ["...", "..."], "correct": [0, 2] }
    ]
  }
}
```
`correct` is a list of 0-based indices into `answers`. `lesson` is the BSI lesson number (2–9); together with `number` it gives the full BSI enumeration shown in the quiz header (e.g. `2.3`). Lektion 1 has no test and is silently skipped.

**`quiz.py`** — Textual TUI with three screens:

| Screen | Role |
|--------|------|
| `MenuScreen` | Category picker via `OptionList`; `s` toggles shuffle |
| `QuizScreen` | Question + `AnswerList` checkboxes; `enter` submits or advances; after submit the list is hidden and a feedback `Static` shown in its place; header shows BSI enumeration e.g. `2.3` |
| `ScoreScreen` | Final result; `r` retry, `m` menu, `q` quit |

Screen stack: `MenuScreen` → `push` → `QuizScreen` → `switch_screen` → `ScoreScreen`. Retry/menu from ScoreScreen uses `switch_screen` / `pop_screen` to return to the right level. CSS lives in the module-level `CSS` string. `ctrl+c` is bound at `App` level with `priority=True` to guarantee clean exit from any screen.

## Data source

Questions come from `https://www.bsi.bund.de` (official BSI site). Lektion 1 (Einstieg) has no test page and is silently skipped; all other 8 lessons (2–9) are scraped. The scraped JSON lives in `data/` so the quiz works offline after the first scrape.
