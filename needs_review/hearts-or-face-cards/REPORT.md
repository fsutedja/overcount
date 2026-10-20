# Needs review: hearts-or-face-cards

Verified on 2026-10-20. 3 problem(s) found.

- **schema** · `hearts-or-face-cards`: only 2 valid instances; need at least 5
- **schema** · `hearts-or-face-cards-red`: only 3 valid instances; need at least 5
- **schema** · `hearts-or-face-cards-exclusive`: only 2 valid instances; need at least 5

## How to fix

1. Open `family.json` and `checker.py` in this folder and fix the issues above.
2. Re-run `uv run overcount verify needs_review/hearts-or-face-cards` (from `pipeline/`) until it passes.
3. Move it into the bank with `uv run overcount promote hearts-or-face-cards`.
