# Overcount

**Practice combinatorics and probability one decision at a time.**

Most counting mistakes aren't arithmetic. They're overcounting, undercounting, or picking the
wrong formula. Overcount lets you answer freely first; when you're stuck, it shows the answer's
structure as a one-line formula with empty boxes to fill in, explains *why* step by step, and
only then shows the worked solution. Answers are math expressions like `C(7,3)·C(5,2)`, graded
by exact value, so any equivalent form counts.

> 🚧 Work in progress. The MVP is being built milestone by milestone.

## How it works

```
generate  →  verify  →  publish
(Gemini      (brute-force     (static bank of
 free tier)   checker +        verified problem
              simulation)      instances)
```

- **Generate:** problem *families* (a root problem plus harder variants, each a template with
  variables and ranges) are drafted with the Gemini API free tier. A reply that fails any check
  is sent back with the problems found, up to twice.
- **Verify:** each family comes with a small Python checker that lists every candidate outcome
  and decides which ones count. Counting those outcomes must equal the answer formula on many
  number sets, every ✅/❌ example must be a real outcome that does / doesn't count, and every
  fill-in skeleton must add up to the answer. Probability problems with unequal chances use a
  Monte Carlo simulation. The checker runs in a sandbox, and nothing is published until a
  person approves it.
- **Publish:** approved families become ~100 concrete number sets each, with examples, outcome
  diagrams, Help steps and a worked small case, shipped as static JSON. The site makes no
  runtime AI calls and costs $0 to serve.

## Learning features

- **Examples and diagrams:** every problem shows one outcome that counts and one that doesn't,
  drawn as a small diagram (dice, cards, beads on a circle, stars and bars, …).
- **Fill in the blanks → Help → Show solution:** blanks for every number, then "why" steps one
  at a time, then the worked answer with this problem's numbers.
- **Practice by method:** 19 counting methods, each with a short lesson (formulas checked by
  brute force) and its own problem list.
- **Progress:** each try is saved in your browser; tries show as dots, and a problem is
  *mastered* when solved within two tries.

## Roadmap

**v1, a live practice site**
- ✅ Playable problems with an answer-first flow, Help blanks and exact grading
- ✅ A content pipeline: Gemini drafts → automatic verification → publish
- 🔄 Practice by method, with saved progress and Σ notation
- ⏭️ Roadmap home page, diagrams (incl. a card-deck grid), more problems, deploy

**v2 and later**
- A tutor chat: "Ask about this step"
- Login, with progress synced across devices
- Streaks and solved-per-difficulty stats
- Weak spots, tutorials and "Fix my weak spots"
- Your own problems (private first)
- Machine learning to predict difficulty and recommend the next problem

## Stack

| Part | Tech |
|---|---|
| Pipeline | Python 3.12, uv, Pydantic, SymPy, google-genai |
| Web | Vite, React, TypeScript, Tailwind, MathLive + Compute Engine, KaTeX |
| Hosting | Vercel (static) |

## Development setup

```bash
pre-commit install          # gitleaks secret scan on every commit
cp .env.example .env        # add your Gemini API key (pipeline only)
```

More setup instructions will be added as the pipeline and web app land.

## Security

- The only secret (`GEMINI_API_KEY`) lives in a gitignored `.env` and is read only by the
  Python pipeline. It is never exposed to the browser bundle.
- [gitleaks](https://github.com/gitleaks/gitleaks) runs as a pre-commit hook and in CI.
