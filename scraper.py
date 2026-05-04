"""Scrapes BSI IT-Grundschutz online course test questions and answers."""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.bsi.bund.de"
COURSE_PATH = (
    "/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/"
    "IT-Grundschutz/Zertifizierte-Informationssicherheit/IT-Grundschutzschulung/"
    "Online-Kurs-IT-Grundschutz"
)

LESSONS = [
    ("Lektion_1_Einstieg", "1", "Einstieg"),
    ("Lektion_2_Sicherheitsmanagement", "2", "Sicherheitsmanagement"),
    ("Lektion_3_Strukturanalyse", "3", "Strukturanalyse"),
    ("Lektion_4_Schutzbedarfsfeststellung", "4", "Schutzbedarfsfeststellung"),
    ("Lektion_5_Modellierung", "5", "Modellierung"),
    ("Lektion_6_IT-Grundschutz-Check", "6", "IT-Grundschutz-Check"),
    ("Lektion_7_Risikoanalyse", "7", "Risikoanalyse"),
    ("Lektion_8_Umsetzungsplanung", "8", "Umsetzungsplanung"),
    ("Lektion_9_Aufrechterhaltung", "9", "Aufrechterhaltung und Verbesserung"),
]


def make_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (educational/research; BSI-prep)"})
    return s


def fetch(url, session, retries=3):
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.encoding or "utf-8"
            return resp.text
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            print(f"    Retry {attempt + 1}/{retries} for {url}: {e}")
            time.sleep(2**attempt)


def find_test_urls(lesson_dir, lesson_num, session):
    """Return (lesson_url, fragen_url, loesungen_url) by scraping the lesson index page."""
    lesson_url = f"{BASE_URL}{COURSE_PATH}/{lesson_dir}/Lektion_{lesson_num}_node.html"
    html = fetch(lesson_url, session)
    soup = BeautifulSoup(html, "html.parser")

    fragen_url = loesungen_url = None
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        # BSI hrefs are root-relative but omit the leading slash
        base = BASE_URL + "/"
        full = urljoin(base, str(href))
        if re.search(r"[Ff]ragen", text):
            fragen_url = full
        elif re.search(r"[Ll][öo][s]ung", text):
            loesungen_url = full

    return lesson_url, fragen_url, loesungen_url


def clean_text(tag):
    """Extract text from a tag, normalising whitespace and BSI hyphen-splitting artifacts."""
    text = re.sub(r"\s+", " ", tag.get_text(separator=" ")).strip()
    # BSI HTML splits compound words across inline tags, creating spaces around hyphens
    # cspell:disable-next-line
    text = re.sub(r"([A-Za-zÄÖÜäöüß0-9])\s*-\s*([A-Za-zÄÖÜäöüß0-9])", r"\1-\2", text)
    return text


def parse_solutions(html):
    """Extract questions with correct answers from a Lösungen page."""
    soup = BeautifulSoup(html, "html.parser")
    questions = []

    frage_headings = [
        tag
        for tag in soup.find_all(re.compile(r"^h[2-4]$"))
        if re.search(r"Frage\s+\d+", tag.get_text())
    ]

    for heading in frage_headings:
        m = re.search(r"Frage\s+(\d+)", heading.get_text())
        if not m:
            continue

        answers: list[str] = []
        correct: list[int] = []
        q: dict = {
            "number": int(m.group(1)),
            "question": "",
            "answers": answers,
            "correct": correct,
        }

        heading_level = int(heading.name[1])
        node = heading.next_sibling

        while node:
            if not isinstance(node, Tag):
                node = node.next_sibling
                continue

            # Stop at the next heading of equal or higher importance
            if re.match(r"^h[1-4]$", node.name) and int(node.name[1]) <= heading_level:
                break

            # Grab question text from first non-empty block before the answer list
            if node.name in ("p", "strong", "b") and not q["question"]:
                text = clean_text(node)
                if text:
                    q["question"] = text

            # Parse answer list
            if node.name in ("ol", "ul"):
                for li in node.find_all("li", recursive=False):
                    raw = clean_text(li)
                    is_correct = "[richtig]" in raw
                    clean = raw.replace("[richtig]", "").strip()
                    idx = len(answers)
                    answers.append(clean)
                    if is_correct:
                        correct.append(idx)

            node = node.next_sibling

        if q["answers"]:
            questions.append(q)

    return questions


def scrape_all(verbose=True):
    session = make_session()
    data = {}

    for lesson_dir, lesson_num, category in LESSONS:
        if verbose:
            print(f"  {category}...", end=" ", flush=True)

        try:
            lesson_url, fragen_url, loesungen_url = find_test_urls(lesson_dir, lesson_num, session)
        except Exception as e:
            print(f"index page error: {e}")
            continue

        if not loesungen_url:
            print("no test found")
            continue

        try:
            html = fetch(loesungen_url, session)
            questions = parse_solutions(html)
        except Exception as e:
            print(f"parse error: {e}")
            continue

        if questions:
            data[category] = {
                "lesson": int(lesson_num),
                "lesson_url": lesson_url,
                "test_url": fragen_url,
                "loesungen_url": loesungen_url,
                "questions": questions,
            }
            print(f"{len(questions)} Fragen")
        else:
            print(f"0 Fragen parsed (URL: {loesungen_url})")

        time.sleep(1)

    return data


def main():
    print("BSI Grundschutz – Fragen scrapen\n")
    Path("data").mkdir(exist_ok=True)
    data = scrape_all()

    Path("data/questions.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    total = sum(len(v["questions"]) for v in data.values())
    print(f"\nGespeichert: {total} Fragen in {len(data)} Kategorien → data/questions.json")


if __name__ == "__main__":
    main()
