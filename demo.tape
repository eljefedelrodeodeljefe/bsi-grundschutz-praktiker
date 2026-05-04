# BSI IT-Grundschutz Praktiker — terminal demo
# Usage: vhs demo.tape
# Requires: just quiz working (data/questions.json present)

Output docs/demo.gif

Set Shell      bash
Set FontSize   14
Set Width      1200
Set Height     700
Set Theme      "TokyoNight"
Set Padding    20
Set TypingSpeed 70ms
Set PlaybackSpeed 1.0

# ── launch ────────────────────────────────────────────────────────────────────

Type "just quiz"
Enter
Sleep 3s

# ── menu: categories with lesson numbers visible ───────────────────────────────

Sleep 1.5s

# disable shuffle so feedback is deterministic, then pick Sicherheitsmanagement
Type "s"
Sleep 400ms
Enter
Sleep 2.5s

# ── question 2.1 — two correct answers ────────────────────────────────────────

# tick answer 1 (index 0)
Space
Sleep 500ms
# move to answer 3 (index 2) and tick it
Down
Sleep 200ms
Down
Sleep 200ms
Space
Sleep 500ms
# submit — both correct answers selected → Richtig!
Enter
Sleep 2s

# correct feedback visible — advance
Enter
Sleep 1s

# ── question 2.2 ──────────────────────────────────────────────────────────────

# skip wrong answer — just submit empty to show the ✗ feedback cleanly
Enter
Sleep 2s

# wrong feedback — advance
Enter
Sleep 1s

# ── quit back to menu ─────────────────────────────────────────────────────────

Type "q"
Sleep 1.5s
