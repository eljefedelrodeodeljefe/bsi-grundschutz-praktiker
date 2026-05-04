"""Persistent storage for quiz attempt results."""

import json
from datetime import UTC, datetime
from pathlib import Path

RESULTS_FILE = Path("data/results.json")


def _load() -> dict:
    if not RESULTS_FILE.exists():
        return {"sessions": [], "questions": {}}
    return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    RESULTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def record_session(category: str, answers: list[dict]) -> None:
    """Persist one completed session and update per-question running totals."""
    data = _load()

    data["sessions"].append(
        {
            "ts": datetime.now(UTC).isoformat(),
            "category": category,
            "score": sum(1 for a in answers if a["correct"]),
            "total": len(answers),
        }
    )

    for a in answers:
        key = a["key"]
        if key not in data["questions"]:
            data["questions"][key] = {
                "category": a["category"],
                "number": a["number"],
                "text": a["text"],
                "attempts": 0,
                "correct_count": 0,
            }
        data["questions"][key]["attempts"] += 1
        if a["correct"]:
            data["questions"][key]["correct_count"] += 1

    _save(data)


def reset() -> None:
    """Wipe all recorded sessions and per-question stats."""
    _save({"sessions": [], "questions": {}})


def get_recent_sessions(n: int = 10) -> list[dict]:
    return _load()["sessions"][-n:]


def get_worst_questions(n: int = 10) -> list[dict]:
    """Questions sorted by success rate ascending (worst first), min 1 attempt."""
    questions = _load()["questions"]
    stats = [
        {
            "category": q["category"],
            "number": q["number"],
            "text": q["text"],
            "attempts": q["attempts"],
            "correct": q["correct_count"],
            "rate": q["correct_count"] / q["attempts"],
        }
        for q in questions.values()
        if q["attempts"] > 0
    ]
    stats.sort(key=lambda x: (x["rate"], -x["attempts"]))
    return stats[:n]
