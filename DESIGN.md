# Overcount design decisions

Overcount is a learning tool first. Every visual choice should help people understand
combinatorics and probability: one problem in focus, a clear step flow, readable math, and an
obvious next action. The personality is lightly inspired by Overcooked: order-ticket cards and
ingredient-style step icons. It uses none of the game's assets, and there are no timers or
urgency mechanics.

Decisions are made at checkpoints. Each checkpoint compares 2–3 rendered options and records
the pick here with its rationale.

## D1 · Palette and type (decided 2026-10-20)

### Palette

Light mode is **Pantry** and dark mode is **Late shift**. The header has a toggle. The default
follows `prefers-color-scheme`, and the user's explicit choice is remembered.

| Token | Light · Pantry | Dark · Late shift | Use |
|---|---|---|---|
| `bg` | `#F4EFE6` | `#1F1D1A` | Page background |
| `card` | `#FFFBF3` | `#2A2723` | Ticket and card surface |
| `border` | `#E4D9C6` | `#3A362F` | Hairlines and ticket edges |
| `ink` | `#2B2823` | `#EEE7DA` | Body text and math |
| `ink-muted` | `#675F53` | `#B3AA9B` | Secondary text |
| `accent` | `#4F8F87` | `#5FA69C` | Input focus, fills |
| `accent-ink` | `#276660` | `#7CC1B7` | Accent text, links, primary button |
| `on-accent` | `#FFFBF3` | `#1F1D1A` | Text on the primary button |
| `deco` | `#C2734F` | `#D99474` | Terracotta. **Decoration only** (logo, ticket stubs), never status |
| `correct-bg` / `correct-ink` | `#E1ECD8` / `#35652F` | `#2C3A28` / `#A6CF99` | Correct feedback |
| `wrong-bg` / `wrong-ink` | `#F3E0E7` / `#8E3352` | `#3E2730` / `#EBA5BC` | Wrong feedback (berry, not red) |

Why:
- The warm, low-contrast surfaces keep the page calm, while text and math still meet WCAG AA.
  An automated contrast test enforces this.
- "Wrong" is berry rather than red, so it can't be mistaken for the terracotta decoration. It
  also stays distinguishable from sage for red/green colour-blind users.
- Feedback is never shown by colour alone. It always includes an icon and a word
  ("✓ Correct" / "✗ Not quite").

### Logo

The `overcount` wordmark is set in Pixelify Sans and split into two tones: teal and
terracotta. The stat line under it is ink.

| Part | Light | Dark |
|---|---|---|
| `over` | `accent-ink` `#276660` | `accent-ink` `#7CC1B7` |
| `count` | terracotta `#C2734F` (`deco`) | `#D99474` (`deco`) |
| Stat line ("5 day streak · 12 solved") | `ink` `#2B2823` | `ink` `#EEE7DA` |

Why: the two-tone split keeps the warm terracotta, and teal replaces black on "over", so black
never sits next to orange. All colours come from existing palette tokens. The ink stat line
reads as plain text, which keeps the header calm.

Alternatives compared: black + terracotta (the original), tonal teal, solid teal, teal + sage,
ink + teal, teal + saffron, and deep teal + terracotta.

### Logo mark

The mark is a 20×20 pixel-art drawing of a black frying pan, seen from a three-quarter angle.
A fried egg flips out of it: half inside the pan, tilted mid-toss. It sits to the left of the
wordmark in the header.

- Files: `web/src/assets/logo-mark.svg` (cropped for the header) and `web/public/favicon.svg`
  (square).
- Colours: pan `#2B2823` / `#3E3A33` with a `#5A544B` rim; egg white `#FFFBF3` with a
  `#C9BBA3` outline; yolk `#E3A13B` with a `#F6CD78` highlight. The yolk yellow is **logo-only**
  and never used for UI states.
- Meaning: a flipped egg is cooked "over easy" (**over**count), and a flip is a coin toss, the
  starting point of probability.
- Concepts considered: an egg carton (choose 3 of 6), Pascal's pan, a binomial egg, several
  side-view tosses, and higher viewing angles. The user chose the simplest version: no motion
  lines, with the egg lowered to sit half inside the pan.

### Type

| Role | Font |
|---|---|
| Body, UI, buttons, inputs, explanations | **Atkinson Hyperlegible** |
| Logo and small UI words (stat labels such as "day streak", "solved") | **Pixelify Sans** |
| **All digits**, including inside Pixelify text (streak, solved counts) | **Atkinson Hyperlegible** Bold at **88%** of the surrounding size |
| Math | KaTeX / MathLive's own math fonts |

Why:
- Atkinson Hyperlegible was designed to make similar characters (1/l/I, 0/O, 5/8) easy to tell
  apart, which matters on a site full of numbers.
- Pixelify Sans gives the logo and stat labels a friendly lowercase pixel personality, but its
  digits are hard to read: 5 looks like 8, and 12 looks like 18. So no digit is ever drawn in
  Pixelify.
- At 88% the digits match the Pixelify lowercase height, so they sit evenly in the line. Of the sizes
  compared (105%, 95%, 88% and 80%), this one was chosen.

Implementation: one composite family, `Overcount Pixel`, defined by two `@font-face` rules.
1. Atkinson Hyperlegible Bold with `unicode-range: U+0030-0039` and `size-adjust: 88%`.
2. Pixelify Sans for everything else.

Any element using the pixel font gets Atkinson digits automatically, so nobody has to wrap
numbers by hand.

Considered and dropped: VT323, Sixtyfour, Doto, DotGothic16, Silkscreen, Jersey 10 and Press
Start 2P.

### Header navigation

The selected page is marked with a 2px teal (`accent-ink`) text underline, offset 4px. Because
it's a text decoration, it doesn't move the link, so every nav item stays on the same line
whichever page is active. Unselected links use `ink-muted`.

### Answer feedback

- **Correct:** a `correct-bg` box with `correct-ink` text reading "✓ Correct. That's 840." The
  computed value is the bonus number. There is no "served" label or celebration graphic; the
  feedback stays plain and calm.
- **Wrong:** a `wrong-bg` box with `wrong-ink` text that starts "✗ Not quite." and ends with a
  hint.
- **Input that can't be graded** (empty, incomplete, letters, too large): a neutral
  `ink-muted` message, not marked wrong.

## D2 · Problem page

Pending (before milestone 2).

## D3 · Home and progress

Pending (before milestone 9).
