# Overcount

**Practice combinatorics and probability one decision at a time.**

Most counting mistakes aren't arithmetic. They're overcounting, undercounting, or picking the
wrong formula. Overcount breaks each problem into fill-in-the-blank steps ("choose ? of ?",
"× or +?", "overcounted? divide by ?") so you can see exactly where your reasoning goes wrong.
Answers are math expressions like `C(7,3)·C(5,2)`, graded by value, so any equivalent form
counts.

> 🚧 Work in progress. The MVP is being built milestone by milestone.

## How it works

```
generate  →  verify  →  publish
(Gemini      (brute-force     (static bank of
 free tier)   checker +        verified problem
              simulation)      instances)
```

- **Generate:** problem *templates* (variables + ranges + step scaffold + a Python checker) are
  drafted with the Gemini API free tier, behind a pluggable `Generator` interface.
- **Verify:** every template is checked by its own brute-force checker across many random
  variable settings (plus Monte Carlo simulation for probability problems). Failures go to
  `needs_review/` for manual fixing.
- **Publish:** verified templates are expanded into thousands of concrete problems, shipped as
  static JSON. The site makes no runtime AI calls and costs $0 to serve.

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
