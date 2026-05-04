"""BSI IT-Grundschutz quiz – Textual TUI."""

import json
import random
import sys
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.events import Key
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, ListItem, ListView, OptionList, Rule, Static
from textual.widgets._option_list import Option

DATA_FILE = Path("data/questions.json")

CSS = """
/* ── shared ── */
Rule {
    color: $primary-darken-3;
    margin: 0;
}

/* ── menu ── */
MenuScreen {
    align: center middle;
}

#menu-container {
    width: 72;
    height: auto;
    padding: 1 2;
}

#app-title {
    text-align: center;
    color: $primary;
    text-style: bold;
    padding-bottom: 0;
}

#app-subtitle {
    text-align: center;
    color: $text-disabled;
    padding-bottom: 1;
}

OptionList {
    height: auto;
    max-height: 18;
    border: round $primary-darken-2;
    margin: 1 0;
}

#shuffle-label {
    text-align: center;
    padding-top: 1;
}

/* ── quiz ── */
#quiz-header {
    padding: 1 2 0 2;
}

#question-text {
    padding: 1 2;
    border: round $primary-darken-1;
    margin: 1 2;
    height: auto;
}

AnswerList {
    height: auto;
    border: none;
    margin: 0 2;
    padding: 0;
}

AnswerItem {
    height: auto;
    padding: 0 1;
}

AnswerItem > Static {
    width: 100%;
    height: auto;
}

AnswerItem.answer-selected > Static {
    color: $primary;
    text-style: bold;
}

#feedback {
    padding: 1 2;
    margin: 0 2;
    height: auto;
}

/* ── score ── */
#score-scroll {
    padding: 1 3;
}

#score-title {
    color: $primary;
    text-style: bold;
    padding-bottom: 1;
}

#score-value {
    padding: 0 0 1 0;
}

.section-heading {
    text-style: bold;
    padding: 1 0 0 0;
}

DataTable {
    height: auto;
    margin: 0 0 1 0;
}

/* ── links screen ── */
LinksScreen {
    align: center middle;
}

#links-container {
    width: 78;
    height: auto;
    padding: 1 2;
}

#links-title {
    color: $primary;
    text-style: bold;
    padding-bottom: 0;
}

#links-hint {
    text-align: center;
    padding-top: 1;
}

/* ── confirm modal ── */
ConfirmModal {
    align: center middle;
}

#confirm-dialog {
    width: 50;
    height: auto;
    padding: 1 2;
    border: round $warning;
    background: $surface;
}

#confirm-message {
    text-align: center;
    padding-bottom: 1;
}

#confirm-buttons {
    align: center middle;
    height: auto;
}

#confirm-buttons Button {
    margin: 0 1;
}
"""


class AnswerItem(ListItem):
    """One answer option rendered as a single wrapping Static."""

    def __init__(self, idx: int, text: str) -> None:
        super().__init__()
        self.idx = idx
        self.answer_text = text
        self.is_ticked = False

    def compose(self) -> ComposeResult:
        yield Static(self._label())

    def _label(self) -> str:
        mark = "☑" if self.is_ticked else "☐"
        return f"{mark} [dim]{self.idx + 1}.[/]  {self.answer_text}"

    def toggle(self) -> None:
        self.is_ticked = not self.is_ticked
        self.query_one(Static).update(self._label())
        self.set_class(self.is_ticked, "answer-selected")


class AnswerList(ListView):
    """ListView of AnswerItems; space toggles the highlighted item."""

    def on_key(self, event: Key) -> None:
        if event.key == "space":
            item = self.highlighted_child
            if isinstance(item, AnswerItem):
                item.toggle()
                event.stop()

    def reset(self, answers: list[str]) -> None:
        self.clear()
        self.mount(*[AnswerItem(j, ans) for j, ans in enumerate(answers)])
        self.call_after_refresh(lambda: setattr(self, "index", 0))

    @property
    def selected_indices(self) -> set[int]:
        return {item.idx for item in self.query(AnswerItem) if item.is_ticked}


class ConfirmModal(ModalScreen[bool]):
    """A yes/no confirmation dialog that returns True on confirm."""

    BINDINGS = [
        Binding("y,enter", "confirm", show=False),
        Binding("n,escape", "cancel", show=False),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Static(self.message, id="confirm-message")
            with Vertical(id="confirm-buttons"):
                yield Button("Ja", id="yes-btn", variant="error")
                yield Button("Nein", id="no-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes-btn")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


BSI_LINKS = [
    {
        "id": "std-200-1",
        "label": "BSI-Standard 200-1",
        "desc": "Managementsysteme für Informationssicherheit (ISMS)",
        "url": (
            "https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/"
            "IT-Grundschutz/BSI-Standards/BSI-Standard-200-1-Managementsysteme-fuer-Informationssicherheit/"
            "bsi-standard-200-1-managementsysteme-fuer-informationssicherheit_node.html"
        ),
    },
    {
        "id": "std-200-2",
        "label": "BSI-Standard 200-2",
        "desc": "IT-Grundschutz-Methodik",
        "url": (
            "https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/"
            "IT-Grundschutz/BSI-Standards/BSI-Standard-200-2-IT-Grundschutz-Methodik/"
            "bsi-standard-200-2-it-grundschutz-methodik_node.html"
        ),
    },
    {
        "id": "std-200-3",
        "label": "BSI-Standard 200-3",
        "desc": "Risikomanagement",
        "url": (
            "https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/"
            "IT-Grundschutz/BSI-Standards/BSI-Standard-200-3-Risikomanagement/"
            "bsi-standard-200-3-risikomanagement_node.html"
        ),
    },
    {
        "id": "std-200-4",
        "label": "BSI-Standard 200-4",
        "desc": "Business Continuity Management (BCM)",
        "url": (
            "https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/"
            "IT-Grundschutz/BSI-Standards/BSI-Standard-200-4-Business-Continuity-Management/"
            "bsi-standard-200-4_Business_Continuity_Management_node.html"
        ),
    },
    {
        "id": "kompendium",
        "label": "IT-Grundschutz-Kompendium",
        "desc": "Bausteine und Anforderungen (Edition 2023, PDF)",
        "url": (
            "https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/"
            "IT-GS-Kompendium/IT_Grundschutz_Kompendium_Edition2023.pdf"
        ),
    },
    {
        "id": "online-kurs",
        "label": "Online-Kurs IT-Grundschutz",
        "desc": "Lernmaterial für die Zertifizierung (Lektionen 1–9)",
        "url": (
            "https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/"
            "IT-Grundschutz/Zertifizierte-Informationssicherheit/IT-Grundschutzschulung/"
            "Online-Kurs-IT-Grundschutz/online-kurs-it-grundschutz_node.html"
        ),
    },
]


def _raw_data() -> dict:
    if not DATA_FILE.exists():
        print("Keine Fragen gefunden. Bitte zuerst 'just scrape' ausführen.")
        sys.exit(1)
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def load_questions() -> dict:
    """Return {category: [questions]} for backward-compatible quiz consumption."""
    return {cat: entry["questions"] for cat, entry in _raw_data().items()}


def load_urls() -> dict:
    """Return {category: {lesson, test}} extracted from the unified data file."""
    if not DATA_FILE.exists():
        return {}
    return {
        cat: {"lesson": entry.get("lesson_url"), "test": entry.get("test_url")}
        for cat, entry in _raw_data().items()
    }


def load_lesson_nums() -> dict[str, int]:
    """Return {category: lesson_number} for header enumeration."""
    if not DATA_FILE.exists():
        return {}
    return {cat: entry["lesson"] for cat, entry in _raw_data().items()}


class LinksScreen(Screen):
    """Overview of BSI reference documents; Enter opens the selected link in the browser."""

    BINDINGS = [
        Binding("escape", "back", "Zurück", show=False),
        Binding("q", "back", "Zurück"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="links-container"):
            yield Static("[bold]BSI Referenz-Dokumente[/]", id="links-title")
            yield Static("↑↓ wählen · ↵ im Browser öffnen · q zurück", id="app-subtitle")
            yield Rule()
            yield OptionList(
                *[
                    Option(
                        f"[bold]{link['label']}[/]  [dim]–  {link['desc']}[/]",
                        id=link["id"],
                    )
                    for link in BSI_LINKS
                ],
                id="links-list",
            )
        yield Footer()

    @on(OptionList.OptionSelected, "#links-list")
    def link_selected(self, event: OptionList.OptionSelected) -> None:
        import webbrowser

        option_id = event.option.id or ""
        for link in BSI_LINKS:
            if link["id"] == option_id:
                webbrowser.open(link["url"])
                break

    def action_back(self) -> None:
        self.app.pop_screen()


class MenuScreen(Screen):
    BINDINGS = [
        Binding("s", "toggle_shuffle", "Shuffle"),
        Binding("x", "reset_scores", "Reset scores"),
        Binding("?", "show_links", "Referenzen"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, data: dict, urls: dict, lesson_nums: dict[str, int]) -> None:
        super().__init__()
        self.data = data
        self.urls = urls
        self.lesson_nums = lesson_nums
        self.shuffle = True

    def compose(self) -> ComposeResult:
        categories = list(self.data.keys())
        all_count = sum(len(v) for v in self.data.values())

        with Vertical(id="menu-container"):
            yield Static("[bold]BSI IT-Grundschutz[/]", id="app-title")
            yield Static(
                "↑↓ wählen · ↵ starten · s mischen · ? referenzen · q beenden", id="app-subtitle"
            )
            yield Rule()
            yield OptionList(
                *[
                    Option(
                        f"[dim]{self.lesson_nums.get(c, '')}.[/]  {c}  [dim]({len(self.data[c])} Fragen)[/]",
                        id=f"cat:{c}",
                    )
                    for c in categories
                ],
                None,
                Option(f"[bold]Alle Kategorien[/]  [dim]({all_count} Fragen)[/]", id="cat:__all__"),
                id="category-list",
            )
            yield Static(self._shuffle_label(), id="shuffle-label")
        yield Footer()

    def _shuffle_label(self) -> str:
        state = "[green]an[/]" if self.shuffle else "[dim]aus[/]"
        return f"[dim]Mischen: {state}[/]"

    @on(OptionList.OptionSelected, "#category-list")
    def category_selected(self, event: OptionList.OptionSelected) -> None:
        option_id = event.option.id or ""
        if option_id == "cat:__all__":
            questions = [{**q, "_category": cat} for cat, qs in self.data.items() for q in qs]
            label = "Alle Kategorien"
        else:
            cat = option_id.removeprefix("cat:")
            questions = [{**q, "_category": cat} for q in self.data[cat]]
            label = cat
        self.app.push_screen(
            QuizScreen(label, questions, self.shuffle, self.urls, self.lesson_nums)
        )

    def action_toggle_shuffle(self) -> None:
        self.shuffle = not self.shuffle
        self.query_one("#shuffle-label", Static).update(self._shuffle_label())

    def action_show_links(self) -> None:
        self.app.push_screen(LinksScreen())

    def action_reset_scores(self) -> None:
        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                from results import reset

                reset()

        self.app.push_screen(ConfirmModal("Alle Ergebnisse löschen?"), on_confirm)

    def action_quit(self) -> None:
        self.app.exit()


class QuizScreen(Screen):
    BINDINGS = [
        Binding("enter", "advance", "Prüfen / Weiter", priority=True),
        Binding("escape", "back", "Menü", show=False),
        Binding("q", "back", "Menü"),
    ]

    def __init__(
        self, category: str, questions: list, shuffle: bool, urls: dict, lesson_nums: dict[str, int]
    ) -> None:
        super().__init__()
        self.category = category
        self.questions = questions.copy()
        if shuffle:
            random.shuffle(self.questions)
        self.idx = 0
        self.score = 0
        self.answered = False
        self.session_answers: list[dict] = []
        self.urls = urls
        self.lesson_nums = lesson_nums
        self._current_urls: dict = {}

    @property
    def current(self) -> dict:
        return self.questions[self.idx]

    def compose(self) -> ComposeResult:
        yield Static("", id="quiz-header")
        yield Rule()
        yield Static("", id="question-text")
        yield AnswerList(id="answer-list")
        yield Static("", id="feedback")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#feedback").display = False
        self._load_question()

    def _load_question(self) -> None:
        self.answered = False
        q = self.current
        total = len(self.questions)

        q_category = q.get("_category", self.category)
        self._current_urls = self.urls.get(q_category, {})
        lesson_num = self.lesson_nums.get(q_category)
        enum = f"{lesson_num}.{q['number']}" if lesson_num else str(q["number"])

        links = ""
        if self._current_urls.get("lesson"):
            links += "  [dim]·[/]  [dim][@click='open_lesson']Lektion ↗[/][/dim]"
        if self._current_urls.get("test"):
            links += "  [dim][@click='open_test']Online-Test ↗[/][/dim]"

        self.query_one("#quiz-header", Static).update(
            f"[bold cyan]{self.category}[/]  [dim]·[/]  "
            f"[dim]{enum}[/]  [dim]·[/]  "
            f"Frage [yellow]{self.idx + 1}[/]/[yellow]{total}[/]  [dim]·[/]  "
            f"Punkte [green]{self.score}[/]/[dim]{self.idx}[/]"
            f"{links}"
        )
        self.query_one("#question-text", Static).update(f"[bold]{q['question']}[/]")

        al = self.query_one("#answer-list", AnswerList)
        al.disabled = False
        al.reset(q["answers"])

        self.query_one("#answer-list").display = True
        self.query_one("#feedback").display = False
        self.call_after_refresh(al.focus)

    def action_advance(self) -> None:
        if not self.answered:
            self._submit()
        else:
            self.idx += 1
            if self.idx >= len(self.questions):
                self.app.switch_screen(
                    ScoreScreen(
                        self.score,
                        len(self.questions),
                        self.category,
                        self.questions,
                        self.session_answers,
                        self.urls,
                        self.lesson_nums,
                    )
                )
            else:
                self._load_question()

    def _submit(self) -> None:
        q = self.current
        al = self.query_one("#answer-list", AnswerList)
        selected = al.selected_indices
        correct = set(q["correct"])
        is_correct = selected == correct

        if is_correct:
            self.score += 1

        q_category = q.get("_category", self.category)
        self.session_answers.append(
            {
                "key": f"{q_category}::{q['number']}",
                "category": q_category,
                "number": q["number"],
                "text": q["question"],
                "correct": is_correct,
            }
        )

        lines = []
        for j, ans in enumerate(q["answers"]):
            chosen = j in selected
            right = j in correct
            mark = "☑" if chosen else "☐"

            if right and chosen:
                lines.append(f"[bold green]{mark}  {j + 1}. {ans}[/]  [green]✓[/]")
            elif right and not chosen:
                lines.append(f"[green]{mark}  {j + 1}. {ans}[/]  [dim]← richtig[/]")
            elif not right and chosen:
                lines.append(f"[bold red]{mark}  {j + 1}. {ans}[/]  [red]✗[/]")
            else:
                lines.append(f"[dim]{mark}  {j + 1}. {ans}[/]")

        result = "[bold green]✓ Richtig![/]" if is_correct else "[bold red]✗ Falsch.[/]"
        self.query_one("#feedback", Static).update("\n".join(lines) + f"\n\n{result}")

        self.query_one("#answer-list").display = False
        self.query_one("#feedback").display = True
        self.answered = True

    def action_open_lesson(self) -> None:
        import webbrowser

        if url := self._current_urls.get("lesson"):
            webbrowser.open(url)

    def action_open_test(self) -> None:
        import webbrowser

        if url := self._current_urls.get("test"):
            webbrowser.open(url)

    def action_back(self) -> None:
        self.app.pop_screen()


class ScoreScreen(Screen):
    BINDINGS = [
        Binding("r", "retry", "Nochmal"),
        Binding("m", "menu", "Menü"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        score: int,
        total: int,
        category: str,
        questions: list,
        session_answers: list[dict],
        urls: dict,
        lesson_nums: dict[str, int],
    ) -> None:
        super().__init__()
        self.score = score
        self.total = total
        self.category = category
        self.questions = questions
        self.session_answers = session_answers
        self.urls = urls
        self.lesson_nums = lesson_nums

    def compose(self) -> ComposeResult:
        pct = self.score / self.total * 100 if self.total else 0
        color = "green" if pct >= 70 else "yellow" if pct >= 50 else "red"
        msg = (
            "[green]Gut gemacht![/]"
            if pct >= 70
            else "[yellow]Fast – noch ein bisschen üben![/]"
            if pct >= 50
            else "[red]Weiter üben – du schaffst das![/]"
        )

        with VerticalScroll(id="score-scroll"):
            yield Static("[bold]Ergebnis[/]", id="score-title")
            yield Rule()
            yield Static(
                f"[{color}][bold]{self.score} / {self.total}[/bold][/]  [dim]({pct:.0f}%)[/]  {msg}",
                id="score-value",
            )
            yield Static("Verlauf", classes="section-heading")
            yield DataTable(id="history-table", show_cursor=False)
            yield Static("Schwächste Fragen", classes="section-heading")
            yield DataTable(id="worst-table", show_cursor=False)
        yield Footer()

    def on_mount(self) -> None:
        from results import get_recent_sessions, get_worst_questions, record_session

        record_session(self.category, self.session_answers)

        # ── session history ──
        ht = self.query_one("#history-table", DataTable)
        ht.add_columns("Datum", "Kategorie", "Score", "Verlauf")
        for s in get_recent_sessions():
            pct = s["score"] / s["total"] * 100 if s["total"] else 0
            color = "green" if pct >= 70 else "yellow" if pct >= 50 else "red"
            filled = round(pct / 10)
            bar = f"[{color}]{'█' * filled}[/][dim]{'░' * (10 - filled)}[/]"
            ht.add_row(
                s["ts"][:10],
                s["category"][:22],
                f"[{color}]{s['score']}/{s['total']}[/]",
                bar,
            )

        # ── worst questions ──
        wt = self.query_one("#worst-table", DataTable)
        wt.add_columns("Kategorie", "Frage", "%", "Versuche")
        for q in get_worst_questions():
            pct = q["rate"] * 100
            color = "green" if pct >= 70 else "yellow" if pct >= 50 else "red"
            text = q["text"][:50] + "…" if len(q["text"]) > 50 else q["text"]
            wt.add_row(
                q["category"][:18],
                text,
                f"[{color}]{pct:.0f}%[/]",
                str(q["attempts"]),
            )

    def action_retry(self) -> None:
        self.app.switch_screen(
            QuizScreen(
                self.category,
                self.questions,
                shuffle=True,
                urls=self.urls,
                lesson_nums=self.lesson_nums,
            )
        )

    def action_menu(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()


class BSIQuizApp(App):
    TITLE = "BSI IT-Grundschutz Quiz"
    CSS = CSS
    BINDINGS = [Binding("ctrl+c", "quit", show=False)]

    def on_mount(self) -> None:
        self.push_screen(MenuScreen(load_questions(), load_urls(), load_lesson_nums()))

    async def action_quit(self) -> None:
        self.exit()


if __name__ == "__main__":
    BSIQuizApp().run()
