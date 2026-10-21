# Polish list

Small "fix later" ideas, so they don't interrupt the current milestone. Pick them up when a
milestone touches the same area, or in milestone 12 (polish and deploy).

## Web
- [x] **Bundle size:** problem pages (Compute Engine + MathLive) now load on demand; the first
  load is ~165 KB gzipped instead of ~1.7 MB. The problem-page chunk is still ~1.55 MB gzipped;
  splitting the Compute Engine further is possible later.
- [ ] **Check `*` → × by hand:** typing `*` in the answer box should insert a × sign. The
  browser tool can't send a real `*` keypress, so this hasn't been verified on a keyboard.
- [ ] **Bank size:** with 5 example pairs per number set, committee-mixed.json is ~360 KB
  (much less gzipped). If it grows, ship extra pairs for fewer number sets or load them lazily.
- [ ] **Help skeleton on phones:** at phone width the one-line skeleton wraps onto two lines.
  Decide whether that's fine or whether the slot boxes should shrink.
- [x] **Skeleton powers and fractions:** done; the skeleton is rendered math with empty boxes as blanks.
- [x] **Slot hint width:** superseded; blanks are now empty boxes with no hints.
- [ ] **Header nav links** (Roadmap, Practice, Progress) are placeholders until milestones 7–9.

- [x] **Mobile nav:** done, a bottom tab bar on phones (DESIGN.md, D15).
- [x] **Σ in the Help skeleton:** done; bounds are stacked blanks.
- [x] **Deploy routing:** `web/vercel.json` rewrites every path to index.html (real files such as
  /bank/*.json are served first), so /practice and /problem/:id work on reload. Set the Vercel
  project's root directory to `web/` when deploying.

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
