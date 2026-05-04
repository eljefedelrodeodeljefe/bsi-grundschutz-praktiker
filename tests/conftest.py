"""Shared fixtures for all test modules."""

import json
from pathlib import Path

import pytest

# Mirrors the new questions.json structure: each category is a dict with
# lesson metadata + questions list.
SAMPLE_DATA: dict = {
    "Sicherheit": {
        "lesson": 2,
        "lesson_url": "https://example.com/lektion2",
        "test_url": "https://example.com/lektion2/test",
        "loesungen_url": "https://example.com/lektion2/loesungen",
        "questions": [
            {
                "number": 1,
                "question": "Was ist IT-Grundschutz?",
                "answers": [
                    "Ein BSI-Standard",
                    "Ein Betriebssystem",
                    "Ein Netzwerkprotokoll",
                    "Ein Backup-Tool",
                ],
                "correct": [0],
            },
            {
                "number": 2,
                "question": "Welche Schutzziele gibt es?",
                "answers": ["Vertraulichkeit", "Verfügbarkeit", "Integrität", "Profitabilität"],
                "correct": [0, 1, 2],
            },
        ],
    },
    "Analyse": {
        "lesson": 3,
        "lesson_url": "https://example.com/lektion3",
        "test_url": "https://example.com/lektion3/test",
        "loesungen_url": "https://example.com/lektion3/loesungen",
        "questions": [
            {
                "number": 1,
                "question": "Was ist Strukturanalyse?",
                "answers": [
                    "Objekte erfassen",
                    "Code schreiben",
                    "Passwörter setzen",
                    "Backups erstellen",
                ],
                "correct": [0],
            },
        ],
    },
}


@pytest.fixture
def sample_questions() -> dict:
    """Return the flat {category: [questions]} view (as load_questions() produces)."""
    return {cat: entry["questions"] for cat, entry in SAMPLE_DATA.items()}


@pytest.fixture
def questions_file(tmp_path: Path) -> Path:
    f = tmp_path / "questions.json"
    f.write_text(json.dumps(SAMPLE_DATA), encoding="utf-8")
    return f


@pytest.fixture
def patch_data_files(questions_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect DATA_FILE to tmp_path for TUI tests."""
    import quiz

    monkeypatch.setattr(quiz, "DATA_FILE", questions_file)


@pytest.fixture
def patch_results_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect RESULTS_FILE to an isolated tmp file."""
    import results

    monkeypatch.setattr(results, "RESULTS_FILE", tmp_path / "results.json")
