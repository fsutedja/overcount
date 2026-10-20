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
- [ ] **Header nav links** (Roadmap, Practice, Progress) are placeholders until milestones 7–9.

## Pipeline
- [ ] **Instance count:** round-table has only 5 instances because `n` runs from 4 to 8.
  Consider a wider range, or accept it for small families.
- [ ] **Generated web types:** the TS types are hand-written and guarded by the cross-check
  test. Generating them from the Pydantic schema is an option later.
