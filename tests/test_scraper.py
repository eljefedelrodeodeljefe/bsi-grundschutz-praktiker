"""Tests for scraper.py — HTML parsing logic."""

from bs4 import BeautifulSoup

from scraper import clean_text, parse_solutions


def _tag(html: str):
    return BeautifulSoup(html, "html.parser")


# ── clean_text ────────────────────────────────────────────────────────────────


def test_clean_text_strips_whitespace():
    tag = _tag("<p>  hello   world  </p>").p
    assert clean_text(tag) == "hello world"


def test_clean_text_joins_across_inline_tags():
    """Inline tags must not produce missing spaces between words."""
    tag = _tag("<p>some <strong>bold</strong> text</p>").p
    assert clean_text(tag) == "some bold text"


def test_clean_text_fixes_hyphen_split():
    """BSI HTML splits compound words across tags, leaving spaces around hyphens."""
    tag = _tag("<p>IT <strong>-Grundschutz</strong>-Check</p>").p
    assert clean_text(tag) == "IT-Grundschutz-Check"


def test_clean_text_preserves_legitimate_hyphens():
    tag = _tag("<p>Plan-Do-Check-Act</p>").p
    assert clean_text(tag) == "Plan-Do-Check-Act"


# ── parse_solutions ───────────────────────────────────────────────────────────

_SINGLE_QUESTION_HTML = """
<html><body>
  <h2>Frage 1:</h2>
  <p><strong>Was ist BSI?</strong></p>
  <ol>
    <li>Eine Behörde [richtig]</li>
    <li>Ein Unternehmen</li>
    <li>Ein Standard</li>
    <li>Ein Protokoll</li>
  </ol>
</body></html>
"""

_MULTI_CORRECT_HTML = """
<html><body>
  <h2>Frage 3:</h2>
  <p>Welche Schutzziele sind klassisch?</p>
  <ol>
    <li>Vertraulichkeit [richtig]</li>
    <li>Profitabilität</li>
    <li>Verfügbarkeit [richtig]</li>
    <li>Integrität [richtig]</li>
  </ol>
</body></html>
"""

_TWO_QUESTIONS_HTML = _SINGLE_QUESTION_HTML.replace("</body>", "") + _MULTI_CORRECT_HTML.replace(
    "<html><body>", ""
)


def test_parse_solutions_single_question():
    questions = parse_solutions(_SINGLE_QUESTION_HTML)
    assert len(questions) == 1
    q = questions[0]
    assert q["number"] == 1
    assert q["question"] == "Was ist BSI?"
    assert len(q["answers"]) == 4
    assert q["correct"] == [0]
    assert "[richtig]" not in q["answers"][0]


def test_parse_solutions_multiple_correct():
    questions = parse_solutions(_MULTI_CORRECT_HTML)
    assert len(questions) == 1
    assert questions[0]["correct"] == [0, 2, 3]


def test_parse_solutions_multiple_questions():
    questions = parse_solutions(_TWO_QUESTIONS_HTML)
    assert len(questions) == 2
    assert questions[0]["number"] == 1
    assert questions[1]["number"] == 3


def test_parse_solutions_strips_richtig_from_answer_text():
    questions = parse_solutions(_SINGLE_QUESTION_HTML)
    for ans in questions[0]["answers"]:
        assert "[richtig]" not in ans


def test_parse_solutions_no_questions_returns_empty():
    assert parse_solutions("<html><body><p>Kein Test hier.</p></body></html>") == []


def test_parse_solutions_question_without_answers_is_skipped():
    html = """
    <html><body>
      <h2>Frage 1:</h2>
      <p>Frage ohne Antworten</p>
    </body></html>
    """
    assert parse_solutions(html) == []
