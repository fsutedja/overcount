# Overcount: standing rules for Claude Code

## Start of every session
- Read CLAUDE.md, PLAN.md (incl. Status), DESIGN.md, POLISH.md and the
  git log first. Tell me which milestone we're on before doing anything.

## Git
- Commit after each milestone with a clear conventional message.
- NEVER push without asking me first.
- No attribution lines in commits or PRs.

## Working style
- I'm learning: explain decisions briefly; answer "why" questions concisely.
- One milestone at a time. Small "fix later" ideas go into POLISH.md.
- If unsure what I want, ask before building.

## Design (I decide visuals)
- Never pick colors, fonts or layouts yourself: show me 2–3 options and wait.
- Record every decision in DESIGN.md.
- Purpose first: the UI helps people understand combinatorics. Light
  Overcooked-inspired touches only, no game assets or game UI.
- Fonts: Pixelify Sans only for the logo and small stat labels ("day streak",
  "solved"). Atkinson Hyperlegible for everything else: body, buttons,
  math, and ALL numbers (incl. streak/solved counts).
- Logo colors: "over" in teal, "count" in terracotta. No black + orange.
- Layout: two panes (problem + visual left, answer right), one column on phones.
- No "served" label; feedback is just "✓ Correct. That's N."

## Product
- Answer-first: free answer box → wrong/"Help" → numbered "why" steps (one at
  a time) that build to a one-line skeleton with empty-box blanks → last resort
  "Show solution" (read-only steps).
- Answers are expressions graded by exact value; number shown only at the end.

## Tech decisions
- Python 3.14. Content parsed with the safe parser (no sympy eval).
- Web types are hand-written, checked by the cross-check test.

## Cost & security
- $0: no paid APIs. Gemini free tier only, via the pipeline (later a
  server-side function). Never put API keys in chat, code, or VITE_ vars.
- Never print or commit .env. Keep gitleaks checks passing.
