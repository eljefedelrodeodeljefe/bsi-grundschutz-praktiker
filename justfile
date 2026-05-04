default: quiz

# Install dependencies
install:
    uv sync

# Scrape questions from BSI website
scrape:
    uv run python scraper.py

# Run the quiz
quiz:
    uv run python quiz.py

# Run tests
test:
    uv run pytest -v

# Lint and type-check
lint:
    uv run ruff check .
    uv run mypy quiz.py scraper.py results.py

# Format code
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# Spell-check source files
spell:
    npx cspell --no-progress "**/*.py"

# Install pre-commit hooks into git (run once after clone)
hook:
    uv run pre-commit install --hook-type commit-msg --hook-type pre-commit

# Run all pre-commit hooks against every file
check:
    uv run pre-commit run --all-files

# Interactive conventional commit (commitizen)
commit:
    uv run cz commit

# Bump version + update CHANGELOG.md + create git tag
bump:
    uv run cz bump

# Show changelog
changelog:
    uv run cz changelog --dry-run

# ── Git Flow ──────────────────────────────────────────────────────────────────

# Start a feature branch from develop
feature name:
    git checkout develop
    git checkout -b feature/{{name}}

# Finish a feature — merge into develop and delete the branch
feature-finish name:
    git checkout develop
    git merge --no-ff feature/{{name}}
    git branch -d feature/{{name}}

# Start a release branch from develop
release-start version:
    git checkout develop
    git checkout -b release/{{version}}

# Finish a release — merge into main + develop, tag, delete branch
release-finish version:
    git checkout main
    git merge --no-ff release/{{version}}
    git tag -a v{{version}} -m "chore(release): v{{version}}"
    git checkout develop
    git merge --no-ff release/{{version}}
    git branch -d release/{{version}}

# Start a hotfix from main
hotfix name:
    git checkout main
    git checkout -b hotfix/{{name}}

# Finish a hotfix — merge into main + develop, delete branch
hotfix-finish name:
    git checkout main
    git merge --no-ff hotfix/{{name}}
    git checkout develop
    git merge --no-ff hotfix/{{name}}
    git branch -d hotfix/{{name}}

# Scrape then quiz
all: scrape quiz
