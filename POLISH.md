# Polish list

Small "fix later" ideas, so they don't interrupt the current milestone. Pick them up when a
milestone touches the same area, or in milestone 12 (polish and deploy).

## Web
- [ ] **Bundle size:** the JS bundle is about 1.6 MB gzipped, mostly the Compute Engine.
  Lazy-load it (and MathLive) so the first page paints fast. Do this before the deploy.
- [ ] **Check `*` → × by hand:** typing `*` in the answer box should insert a × sign. The
  browser tool can't send a real `*` keypress, so this hasn't been verified on a keyboard.
- [ ] **Help skeleton on phones:** at phone width the one-line skeleton wraps onto two lines.
  Decide whether that's fine or whether the slot boxes should shrink.
- [ ] **Skeleton powers and fractions:** `[a]^[b]` shows a literal `^` between two boxes. Render the
  exponent box raised (and fractions stacked) so the skeleton looks like the math it stands for.
- [x] **Slot hint width:** (fixed in f77fb15: boxes grow to fit, hints capped at 14 characters) longer hints get cut off ("non-sixes" shows as "non-sixe"). Let boxes
  grow to fit their hint, or cap hints at a short length in the prompt and schema.
- [ ] **Header nav links** (Roadmap, Practice, Progress) are placeholders until milestones 7–9.

- [ ] **Mobile nav:** the header links are hidden below 640px, so phones can't reach /practice
  yet. Add a compact menu.
- [ ] **Σ in the Help skeleton:** sums show as plain text "Σ(k=0..[a]) …". Render them as real
  math with boxes in the limits.
- [ ] **Deploy routing:** add a Vercel rewrite to index.html so /practice and /problem/:id work on
  reload.

## Content
- [ ] **Stirling and identical boxes:** balls-into-boxes skips distinct or identical balls into
  *identical* boxes (Stirling numbers, partitions). Add when the grammar supports them.

## CI
- [ ] **Node 20 actions:** `actions/checkout@v4`, `actions/setup-node@v4`, `astral-sh/setup-uv@v6`
  and `gitleaks/gitleaks-action@v2` target the retiring Node 20 (GitHub runs them on Node 24 for
  now). Bump to their Node 24 releases, checking each action's release notes for the exact version.

## Pipeline
- [ ] **Instance count:** round-table has only 5 instances because `n` runs from 4 to 8.
  Consider a wider range, or accept it for small families.
- [ ] **Generated web types:** the TS types are hand-written and guarded by the cross-check
  test. Generating them from the Pydantic schema is an option later.
