"""Tests for results.py — persistence and aggregation."""

import json

import pytest

import results


def _answer(number: int, correct: bool, category: str = "Cat") -> dict:
    return {
        "key": f"{category}::{number}",
        "category": category,
        "number": number,
        "text": f"Q{number}",
        "correct": correct,
    }


# ── empty state ───────────────────────────────────────────────────────────────


def test_empty_sessions(patch_results_file):
    assert results.get_recent_sessions() == []


def test_empty_worst_questions(patch_results_file):
    assert results.get_worst_questions() == []


# ── record_session ────────────────────────────────────────────────────────────


def test_record_session_creates_file(tmp_path, monkeypatch):
    results_file = tmp_path / "results.json"
    monkeypatch.setattr(results, "RESULTS_FILE", results_file)

    results.record_session("Cat", [_answer(1, True)])
    assert results_file.exists()


def test_record_session_score(patch_results_file, tmp_path):
    results.record_session("Cat", [_answer(1, True), _answer(2, False), _answer(3, True)])
    sessions = results.get_recent_sessions()
    assert sessions[0]["score"] == 2
    assert sessions[0]["total"] == 3
    assert sessions[0]["category"] == "Cat"


def test_record_session_updates_question_stats(patch_results_file, tmp_path, monkeypatch):
    results_file = tmp_path / "results.json"
    monkeypatch.setattr(results, "RESULTS_FILE", results_file)

    results.record_session("Cat", [_answer(1, True), _answer(1, False)])
    data = json.loads(results_file.read_text())
    q = data["questions"]["Cat::1"]
    assert q["attempts"] == 2
    assert q["correct_count"] == 1


def test_record_session_accumulates_across_calls(patch_results_file):
    results.record_session("Cat", [_answer(1, True)])
    results.record_session("Cat", [_answer(1, False)])
    sessions = results.get_recent_sessions()
    assert len(sessions) == 2


# ── get_recent_sessions ───────────────────────────────────────────────────────


def test_get_recent_sessions_returns_last_n(patch_results_file):
    for i in range(15):
        results.record_session("Cat", [_answer(i % 6 + 1, i % 2 == 0)])
    assert len(results.get_recent_sessions(10)) == 10
    assert len(results.get_recent_sessions(5)) == 5


def test_get_recent_sessions_default_limit(patch_results_file):
    for _ in range(12):
        results.record_session("Cat", [_answer(1, True)])
    assert len(results.get_recent_sessions()) == 10


# ── get_worst_questions ───────────────────────────────────────────────────────


def test_worst_questions_sorted_by_rate(patch_results_file):
    # Q1: 1/4 = 25 %
    results.record_session("Cat", [_answer(1, True)])
    for _ in range(3):
        results.record_session("Cat", [_answer(1, False)])
    # Q2: 4/4 = 100 %
    for _ in range(4):
        results.record_session("Cat", [_answer(2, True)])

    worst = results.get_worst_questions()
    assert worst[0]["number"] == 1
    assert worst[0]["rate"] == pytest.approx(0.25)
    assert worst[1]["number"] == 2
    assert worst[1]["rate"] == pytest.approx(1.0)


def test_worst_questions_respects_limit(patch_results_file):
    for n in range(1, 15):
        results.record_session("Cat", [_answer(n, n % 2 == 0)])
    assert len(results.get_worst_questions(5)) == 5


def test_worst_questions_excludes_zero_attempts(patch_results_file):
    """Questions that were never answered must not appear."""
    assert results.get_worst_questions() == []


# ── reset ─────────────────────────────────────────────────────────────────────


def test_reset_clears_sessions(patch_results_file):
    results.record_session("Cat", [_answer(1, True)])
    results.reset()
    assert results.get_recent_sessions() == []


def test_reset_clears_questions(patch_results_file):
    results.record_session("Cat", [_answer(1, True)])
    results.reset()
    assert results.get_worst_questions() == []


def test_reset_idempotent_on_empty(patch_results_file):
    results.reset()
    results.reset()
    assert results.get_recent_sessions() == []
