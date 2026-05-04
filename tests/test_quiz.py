"""Tests for quiz.py — widgets and TUI screen flows."""

import pytest
from textual.widgets import OptionList

import quiz
import results
from quiz import (
    AnswerItem,
    AnswerList,
    BSIQuizApp,
    ConfirmModal,
    MenuScreen,
    QuizScreen,
    ScoreScreen,
)

# ── AnswerItem ────────────────────────────────────────────────────────────────


def test_answer_item_initial_state():
    item = AnswerItem(0, "answer text")
    assert not item.is_ticked
    assert "☐" in item._label()
    assert "answer text" in item._label()


def test_answer_item_one_based_index_in_label():
    assert "3." in AnswerItem(2, "x")._label()
    assert "1." in AnswerItem(0, "x")._label()


def test_answer_item_ticked_label():
    item = AnswerItem(0, "text")
    item.is_ticked = True
    assert "☑" in item._label()


def test_answer_item_unticked_label():
    item = AnswerItem(0, "text")
    item.is_ticked = False
    assert "☐" in item._label()


# ── load helpers ──────────────────────────────────────────────────────────────


def test_load_questions_exits_if_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(quiz, "DATA_FILE", tmp_path / "nope.json")
    with pytest.raises(SystemExit):
        quiz.load_questions()


def test_load_urls_returns_empty_if_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(quiz, "DATA_FILE", tmp_path / "nope.json")
    assert quiz.load_urls() == {}


def test_load_urls_extracted_from_questions_file(questions_file, monkeypatch):
    monkeypatch.setattr(quiz, "DATA_FILE", questions_file)
    urls = quiz.load_urls()
    assert "Sicherheit" in urls
    assert urls["Sicherheit"]["lesson"] == "https://example.com/lektion2"
    assert urls["Sicherheit"]["test"] == "https://example.com/lektion2/test"


# ── MenuScreen ────────────────────────────────────────────────────────────────


async def test_menu_shows_categories(patch_data_files, sample_questions):
    app = BSIQuizApp()
    async with app.run_test(headless=True) as _:
        assert isinstance(app.screen, MenuScreen)
        option_list = app.screen.query_one(OptionList)
        # categories + "Alle Kategorien" (None separator doesn't count as an option)
        assert option_list.option_count == len(sample_questions) + 1


async def test_menu_enter_opens_quiz(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert isinstance(app.screen, QuizScreen)


async def test_menu_shuffle_toggle(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True) as pilot:
        menu = app.screen
        assert isinstance(menu, MenuScreen)
        assert menu.shuffle is True
        await pilot.press("s")
        assert menu.shuffle is False
        await pilot.press("s")
        assert menu.shuffle is True


# ── QuizScreen ────────────────────────────────────────────────────────────────


async def test_quiz_initial_state(patch_data_files, sample_questions):
    app = BSIQuizApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.press("enter")
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, QuizScreen)
        assert screen.idx == 0
        assert screen.score == 0
        assert not screen.answered


async def test_quiz_submit_marks_answered(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True, size=(80, 24)) as pilot:
        await pilot.press("enter")
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        await pilot.press("enter")  # submit with no selection
        await pilot.pause(0.1)
        assert screen.answered


async def test_quiz_correct_answer_increments_score(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True, size=(80, 24)) as pilot:
        await pilot.press("s")  # disable shuffle — Q1 always first, correct=[0]
        await pilot.press("enter")
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        al = screen.query_one("#answer-list", AnswerList)
        al.focus()
        await pilot.pause(0.2)
        await pilot.press("space")  # select answer 0 — the only correct one for Q1
        await pilot.press("enter")  # submit
        await pilot.pause(0.1)
        assert screen.score == 1


async def test_quiz_wrong_answer_no_score(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True, size=(80, 24)) as pilot:
        await pilot.press("enter")
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        # Submit with no selection — Q1 correct=[0], so no selection is wrong
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert screen.score == 0


async def test_quiz_advance_to_next_question(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True, size=(80, 24)) as pilot:
        await pilot.press("enter")
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        await pilot.press("enter")  # submit q1
        await pilot.pause(0.1)
        await pilot.press("enter")  # advance
        await pilot.pause(0.1)
        assert screen.idx == 1


async def test_quiz_completes_to_score_screen(
    patch_data_files, patch_results_file, sample_questions
):
    app = BSIQuizApp()
    async with app.run_test(headless=True, size=(80, 30)) as pilot:
        await pilot.press("enter")
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, QuizScreen)
        total = len(screen.questions)

        await pilot.press("enter")  # submit q1
        for _ in range(total - 1):
            await pilot.pause(0.1)
            await pilot.press("enter")  # advance
            await pilot.press("enter")  # submit
        await pilot.pause(0.1)
        await pilot.press("enter")  # advance to score
        await pilot.pause(0.3)
        assert isinstance(app.screen, ScoreScreen)


async def test_quiz_back_returns_to_menu(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.press("enter")
        await pilot.pause(0.2)
        await pilot.press("q")
        await pilot.pause(0.1)
        assert isinstance(app.screen, MenuScreen)


# ── ConfirmModal ──────────────────────────────────────────────────────────────


async def test_confirm_modal_opens_on_x(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.press("x")
        await pilot.pause(0.1)
        assert isinstance(app.screen, ConfirmModal)


async def test_confirm_modal_cancel_keeps_menu(patch_data_files):
    app = BSIQuizApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.press("x")
        await pilot.pause(0.1)
        await pilot.press("n")
        await pilot.pause(0.1)
        assert isinstance(app.screen, MenuScreen)


async def test_confirm_modal_yes_resets_results(patch_data_files, patch_results_file):
    results.record_session(
        "Cat", [{"key": "Cat::1", "category": "Cat", "number": 1, "text": "Q", "correct": True}]
    )
    assert len(results.get_recent_sessions()) == 1

    app = BSIQuizApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.press("x")
        await pilot.pause(0.1)
        await pilot.press("y")
        await pilot.pause(0.1)
        assert isinstance(app.screen, MenuScreen)

    assert results.get_recent_sessions() == []
