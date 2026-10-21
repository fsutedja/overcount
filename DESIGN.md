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

### Layout (decided 2026-10-20): B · Two panes

- **Desktop:** the left pane holds the order ticket (statement) and the picking visual, and stays
  pinned (`position: sticky`) while you scroll. The right pane holds the answer-first flow:
  1. The answer box.
  2. The **Help** skeleton (one line, group labels underneath, a slot hint inside each box).
  3. **Show solution**, as read-only steps with math-symbol icons.

  There is no Guided/Free toggle. The answer-first flow replaced it on 2026-10-20; see PLAN.md.
- **Phones (< 768px):** the panes stack into a single column (layout A): ticket, then visual,
  then the answer and help.
- **Column alignment:** both panes start with a matching heading ("Problem" / "Your answer"), so
  the cards under them line up.
- **Why:** counting problems need constant rereading of the numbers and checking the visual
  against your answer. B keeps both on screen for every step. A lets them scroll away, and C
  hides the statement behind a summary.
- **Mockup:** [design/mockups/d2-problem-layouts.html](design/mockups/d2-problem-layouts.html)
  (all three options compared).

### Step icons (decided 2026-10-20): C · Math symbols

Each step kind shows its operation as a bold symbol in an `accent-soft` tile (`accent-ink`
text), always next to the step's text label.

| Step kind | Symbol | Meaning |
|---|---|---|
| Choose | **C** | unordered selection, C(n, k) |
| Arrange | **P** | ordered selection, P(n, k), n! |
| Combine | **×+** | the "× or +?" decision step |
| Split into cases | **Σ** | separate cases, then add |
| Inclusion–exclusion | **∪** | add the groups, subtract the overlap |
| Complement | **1−** | total minus what you don't want |
| Divide out overcount | **÷** | divide by the number of orderings |
| Condition | **A\|B** | given that B happened |
| Distribution | **∼** | binomial, geometric, … |

- **Rule:** an icon names the *kind* of step and never gives away a blank's answer. That's why
  Combine shows both × and +.
- **Why:** it's the most direct link to the math being learned, and symbols render crisply at
  every size in both themes.
- **Considered and dropped:**
  - Pixel kitchen icons (egg carton, mixing bowl, cleaver, strainer, jars). Several were hard to
    read at 12×12, and the complement icon in particular never landed: pie, ticket, cracked egg,
    shells, loaf, cup, cookie tray and pancake were all tried.
  - Generic line icons.
- **Mockup:** [design/mockups/d2-step-icons.html](design/mockups/d2-step-icons.html)

Split into cases and inclusion–exclusion were added as step kinds during this checkpoint, so
addition and subtraction each have a home: Σ for disjoint cases, ∪ for overlaps, and 1− for
complements.

## D4 · Example and visual ("one outcome" diagram)

**Decided: C · Pantry pieces.**

- Pieces are chunky, with a 2.5px `--ink` outline and a small offset shadow (3px, `--border`).
  They sit on `--card`.
- Highlighted pieces (the part that makes an outcome count, e.g. the 6s) are solid `--accent`,
  with `--on-accent` marks.
- Second colour for two-colour items (beads, bars in stars & bars) is `--deco`.
- Labels under pieces ("roll 1", "box 2: 0") are small and `--ink-muted`.
- The ✅/❌ example lines use the existing correct and wrong tokens.
- The "▾ Example" toggle (accent-ink, bold) opens and closes the example and diagram together.
  It is open by default, and the choice is remembered across problems.
- **Why:** the most playful of the three, a light Overcooked nod (counters on a kitchen
  board), while every piece is still plain math, not a game asset.
- **All 10 types approved** (dev preview at `/dev/visuals`): dice, coins, sequence (optional
  captions), circle, subset, boxes, stars & bars, cards, path (grid, route in accent, start and
  end in deco), matching (items on top, spots below, lines between).
- **Subsets with more than one kind of item** (juniors and seniors) show each kind as its own
  labelled row (no divider line), so they don't look interchangeable.
- **Considered:** A · Tiles (flat, closest to the current UI), B · Line drawing (outlines only).
- **Mockup:** [design/mockups/d4-visual-styles.html](design/mockups/d4-visual-styles.html)

## D5 · Attempts: try dots

**Decided: C · Try dots, without a star.**

- One small mark per try, oldest first: a filled `--correct-ink` dot for right and a hollow
  `--wrong-ink` **ring** for wrong (D10: shape as well as colour, for colour-blind readers). Marks
  stop at the first right answer, so a first-try right answer is a single green dot.
- Mastered (right within 2 tries) and solved (right later) are told apart by the dots alone; no
  star or badge.
- On the problem page, next to the answer prompt: the dots, a **dashed** circle for the next
  try (so it can't be mistaken for a wrong-try ring), and "try N" while unsolved. More than 8 dots collapse into "+n".
- In practice lists, the dots sit at the right end of each row (they replace the ✓).
- **Help nudge:** after 3 wrong tries, "← stuck? try Help" appears beside the Help link in
  `--ink-muted`. It never blocks answering.
- **Considered:** A · Quiet text, B · Chips.
- **Mockup:** [design/mockups/d5-attempts.html](design/mockups/d5-attempts.html)

## D6 · Method lessons ("How it works")

**Decided: C · Tabs, plus a method pill on problems.**

- The method page has two tabs, **Practice** and **Learn**. It always opens on **Practice**;
  Learn is opened by hand. The tab uses the existing underline style (accent-ink, 3px).
- A lesson has: what the method is, how it works, formulas (rendered math, each with when it
  applies), one worked mini example, and a common trap.
- On problem pages the lesson lives in a "Method" tab inside the problem card (see D7). The
  side panel first built for this was dropped: it covered the answer box.
- **Why:** the lesson is one tap away at the moment a learner is stuck; the pill teaches method
  names; Practice-first keeps returning learners one click from problems.
- **Considered:** A · Lesson card above the list, B · Lesson beside the list.
- **Mockup:** [design/mockups/d6-method-explainer.html](design/mockups/d6-method-explainer.html)

## Help skeleton blanks

- The skeleton is rendered math (MathLive, read-only) with editable blanks. Blanks are **empty
  boxes**: no "?" and no hint text. The group labels underneath say what each part counts.
- A wrong blank is **only shaded** with `--wrong-bg` (the berry tint) after checking: no
  strike-through, no ✗, no glow, and its digits stay `--ink`. MathLive's own accent hue is set
  to the teal of `--accent`.

## D7 · Method lesson on the problem page

**Decided: B · Tabs inside the problem card.**

- Under the statement, on **one line**: ▾, **Example** (always the default on every problem), a
  thin vertical divider (`--border`), then one tab per method named by the method alone (at
  most 2; screen readers hear "Method: …"). The row scrolls sideways rather than wrapping. The Method tab shows the lesson in the same space; the answer box
  is never covered or moved.
- The ▾ button at the start of the tab row folds the whole area; that choice is remembered
  across problems (it replaces the old "▾ Example" toggle). Clicking a tab unfolds it.
- Spoiler rule: Method tabs appear at once on problems opened from that method's Practice tab,
  elsewhere only after the first wrong try (or once solved).
- Tabs use the same underline style as the method page tabs.
- **Considered:** A · Lesson unfolds under a pill, C · Short cheat card under the answer box.
- **Mockup:** [design/mockups/d7-lesson-in-page.html](design/mockups/d7-lesson-in-page.html)

## D8 · Progress page

**Decided: C · Tabs, "Overview | Problems".**

- **Overview:** headline numbers (solved, mastered, tries, day streak, best streak; labels in
  Pixelify Sans, numbers in Atkinson), then the activity heatmap and the tries chart on the left
  and progress by roadmap stop on the right (stacked on phones).
- **Activity heatmap, GitHub style:** the last 52 weeks, one column per week (Sunday on top),
  month names above, Mon / Wed / Fri labels on the left, a "Less → More" legend, and a hover
  tooltip with the date and count. Shades: the 4 teal steps used on Home (0, 1, 2, 3+ problems
  solved that day).
- **Tries per day:** two lines over the last 30 days on one axis (both are counts): "tries" as
  a dashed `--ink-muted` line and "right" as a solid `--accent` line, each labelled at its end,
  with a legend and a hover crosshair + tooltip.
- **Problems tab:** filter chips (All, Mastered, Solved, Tried, Not started) and one row per
  problem with its status and try dots, linking to the problem.
- **Considered:** A · One report, B · Two columns.
- **Mockup:** [design/mockups/d8-progress.html](design/mockups/d8-progress.html) (the chart and
  heatmap were changed after review as described above).

## D9 · New numbers

**Decided: A · next to the title, icon only.**

- A "↻" button at the right of the problem title (accent-ink, no text; hover title and screen
  reader label "New numbers"). It's there before and after solving.
- It picks another checked number set of the same problem at random; the page starts fresh
  (blanks, Help, solution reset), while try dots keep counting for the problem. The set is kept
  in the address (`?n=`), so a reload shows the same numbers.
- Hidden when a problem has fewer than 5 number sets.
- **Considered:** B · buttons after solving (incl. "Try a variation"), C · both.
- **Mockup:** [design/mockups/d9-new-numbers.html](design/mockups/d9-new-numbers.html)

## D10 · Try marks for colour-blind readers, and Practice filters

**Try marks: A · wrong tries as rings.** Green and berry fail a deuteranopia check (ΔE 4.1), so
wrong tries are hollow rings and the next try is a dashed circle (see D5).
- **Considered:** B · a small ×.

**Practice filters: C · one chip row with dividers.** On a method's Practice tab: kind chips
(All, Counting, Probability) | difficulty chips (Easy, Medium, Hard; click again to clear) |
a "Context: …" dropdown listing only the contexts that method has. Thin `--border` dividers,
the same as the problem card tabs. Filters live in the address, so they survive a reload.
- **Considered:** A · a row of chips per filter, B · a row of dropdowns.
- **Mockup:** [design/mockups/d10-dots-and-filters.html](design/mockups/d10-dots-and-filters.html)

## D11 · Card-deck grid

**Decided: A · both groups shaded, stripes where they overlap.**

- Card problems that name their groups (`visual.deck_groups`, at most 2) show the 13×4 deck in
  the Example tab instead of the plain row of cards: suits as rows (♥ ♦ ♣ ♠, red suits in
  `--wrong-ink`), ranks as columns.
- The first group is shaded `--accent-soft`, the second `--deco-soft` (new token: light
  terracotta, `#f3e2d8` light / `#3b2c24` dark), cards in both are striped with the two, and
  the ✅ hand's cards get a 2.5px `--ink` outline. "Show another example" moves the outline.
- A legend names each group with its size, "both" and "the ✅ hand", so the groups don't rely on
  colour alone.
- **Considered:** B · only the hand, groups named by edge labels; C · two small decks.
- **Mockup:** [design/mockups/d11-card-deck.html](design/mockups/d11-card-deck.html)

## D12 · Moving between problems

**Decided: B · Problem list on the left.**

- On wide screens (`lg` and up) a narrow column sits left of the problem, its top level with
  the problem card. Top to bottom: "← Back to the list" (or "← All methods"), the list's title,
  then the method's problems in Practice-list order, each with its try marks; the current one
  is highlighted (accent-soft, accent-ink text, a 3px accent-ink bar on the left). It stays in
  view while scrolling.
- Opened from a method's Practice tab, the title is that method's name; from anywhere else it
  says "Related problems" and uses the problem's first method, so the method isn't given away
  (D6 spoiler rule).
- Narrower screens: a "▸ Problems" button above the page unfolds the same list.
- **Considered:** A · back link and previous / next; C · A plus a problem menu.
- **Mockup:** [design/mockups/d12-problem-nav.html](design/mockups/d12-problem-nav.html)

## No emoji

- No emoji in the interface or in learner-facing content. The example lines read
  "**Counts:** …" and "**Doesn't count:** …" (in their correct / wrong boxes), and legends say
  "the hand that counts". Plain text symbols that are part of the type (✓ in "✓ Correct.", ↻, ‹ ›,
  ▾, card suits) are fine. The `family-v3` prompt tells Gemini the same.

## Help flow (answer panel)

- The free answer box comes first. **Fill in the blanks** (accent-ink link, where Help used to be)
  opens the skeleton at once, so you can type straight away.
- With the blanks open, **Help** shows the numbered why-steps under a thin rule ("Help: why it
  works") **one at a time in the same place**, with round ‹ › arrow buttons (accent-ink outline;
  greyed out at either end) and "Step 2 of 4" underneath. ← and → keys work too. The last
  slide is the small-numbers check, stacked one "=" per line so it fits on phones. Slides use
  the D2 step cards.
- **Show solution** (after one wrong try at the blanks) sits right under Help in the same answer
  card, with the same ‹ › arrows, one step at a time: each step's math with this problem's
  numbers and its value, e.g. C(8, 3) = 56, the last one marked "the answer". No explanation
  text, so it never repeats Help.
- The nudge after 3 wrong tries reads "← stuck? fill in the blanks".

## D3 · Home and progress

**Decided (desktop): B · Branching map (NeetCode-style).**

- The 8 roadmap stops are laid out as a small map with connector lines showing which topics
  build on which (Counting basics → Combinations → Stars and bars and Complement →
  Inclusion–exclusion → Probability basics → Conditional and Distributions).
- Each stop is a card with its title, "solved / total" and a progress bar; the stop you're on
  has an accent-ink outline; stops with no problems yet are faded ("coming soon"). Clicking a
  stop opens its methods.
- The side column holds, top to bottom: today's problem, the picked stop (title, blurb and its
  methods as chips with solved / total; the current stop is picked at first), and the activity
  card (day streak, solved, 5-week heatmap, 15 squares per row as in the mockup).
- The daily problem card shows difficulty and kind, not the method (spoiler rule).
- **Phones: A · One path.** The same stops in the same order on one dotted line, with numbered
  dots (finished = filled teal, current = accent-ink outline). The current stop is open and lists
  its methods as chips with solved / total; tapping another stop opens it. Today's problem and
  the activity card sit above the path.
- **Considered:** A · One path, C · Dashboard.
- **Mockup:** [design/mockups/d3-home.html](design/mockups/d3-home.html)
