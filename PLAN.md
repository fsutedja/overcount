# Overcount: Combinatorics & Probability Practice Site, Design Plan

## Status (2026-10-21)

**Done**

| Milestone | What shipped |
|---|---|
| 0 · Repo setup | Private GitHub repo, gitleaks pre-commit hook, `.env.example`, README stub |
| 1 · Playable problem | MathLive input, Compute Engine grading (exact, no mathjs needed), D1 tokens and fonts, light/dark toggle |
| 2 · Answer-first player | Free answer with targeted feedback; Help skeleton; Show solution; attempt records with help level (milestones 2 and 3 merged) |
| 4 · Pipeline core | Pydantic schema, `ast`-whitelisted expression grammar with sympy values and LaTeX, instance builder, `overcount build [--check]`, 3 golden families (6 problems) |
| 5 · Verify | Sandboxed checkers (import/builtin allowlist + isolated process with time and memory limits); schema, brute-force and simulation gates; `verify`, `promote` and `stats`; `needs_review/` reports; GitHub Actions CI |
| 6 · Gemini generator | `overcount generate` with `content/targets.yaml`, the versioned prompt `family-v1`, rate limits, retries with backoff, a clean stop on the daily quota or an unavailable model, and a resumable `data/generation_log.jsonl`. First run: 3 families generated; 2 passed every gate and 1 went to `needs_review/` |
| Design D1, D2 | Palette, type and logo; two-pane layout; math-symbol step icons. See [DESIGN.md](DESIGN.md), which takes precedence over §5b wherever they differ |

**Changed from the original plan**
- **Answer-first flow:** a free answer, then "Fill in the blanks" (a one-line skeleton), then
  Help (why-steps), then Show solution (see Status: Lessons, Help and blanks). This replaced the
  step-by-step player and the Guided/Free toggle, so milestones 2 and 3 became one milestone.
- **Problem format:** steps are now read-only `solution` text. Common mistakes live on the final
  answer, and the skeleton has group labels, slot hints and `slot_mistakes` (see §2a).
- **Step kinds:** `cases` (Σ) and `inclusion-exclusion` (∪) were added, so addition and
  subtraction each have their own kind.
- **Expressions:** content is parsed with Python's `ast` against a whitelist instead of sympy's
  `parse_expr`. That keeps LLM-written content from ever being `eval`'d and gives LaTeX that
  matches the author's structure.
- **Web types:** TypeScript types for the bank are hand-written rather than generated from JSON
  Schema. A vitest cross-check grades every committed answer, skeleton and solution with the
  browser's Compute Engine instead. Generating the types is still possible later.
- **Pushing:** pushes happen only after explicit approval, not automatically after each
  milestone.
- **Python:** developed on 3.14, still compatible with 3.12 and up.
- **Gemini:** the default model is `gemini-3.8-flash`, because `gemini-2.5-flash` is no longer
  offered to new API keys. Retries use a small hand-written loop rather than `tenacity`. Each
  family takes about 2 minutes to generate.
- **Placeholder check:** the schema now rejects malformed `{{x}}` placeholders. Review caught one
  in a generated explanation that the gates had let through.
- **Card problems** (decided 2026-10-20, details in §2a): standard 52-card deck by default and
  exempt from the "at least 5 number sets" rule; variety comes from case variants; custom decks
  are only for Hard problems. The `family-v2` prompt teaches this, and `hearts-or-face-cards`
  passed under it and is published.

- **Practice by method** (2026-10-21): 19 counting methods (`taxonomy.py`), each placed under one
  roadmap node (`content/roadmap.yaml`). There are no separate `/methods` or `/topics` pages.
  `/practice` is a temporary methods list (until the roadmap Home), and `/practice?method=&kind=`
  filters problems. Every problem gets a Counting/Probability kind derived from its primary topic.
  Progress is saved in localStorage behind `ProgressStore` (pulled forward from milestones 7–8).
- **Σ in the grammar** (`Sum(body, k, lo, hi)`) instead of a derangement function; matching
  problems use the Pitman form. Stirling/identical-box cases are out of scope for now.
- **Review before publishing:** generated families stay in `staging/` until `overcount approve`.
  `overcount review` writes a side-by-side page, and `stats` shows the funnel.

- **Examples and visuals on every problem** (2026-10-21, details in §2a "Examples and visuals"):
  every problem shows what one outcome looks like, a ✅ outcome that counts and a ❌ one that
  doesn't, with reasons, plus a small diagram (D4 · Pantry pieces). "Show another example"
  cycles through more pairs. Checkers now list outcomes and decide which count, and the same
  functions verify the answer and every example. The plain-wording rules are in the
  `family-v3` prompt.
- **Attempt tracking** (2026-10-21, §2c): each attempt stores the answer; repeated identical
  answers don't count as new tries; "mastered" means solved within 2 tries; after 3 wrong
  tries the page suggests Help (never blocks).

- **Lessons, Help and blanks** (2026-10-21):
  - A lesson for each of the 19 methods (`content/methods.yaml`, every formula brute-force
    tested). Method pages have Practice | Learn tabs (Practice first); problem cards have
    Example | Method tabs (D6, D7).
  - Help flow: free answer → "Fill in the blanks" opens the skeleton at once (empty boxes, wrong
    ones shaded berry) → "Help" shows numbered why-steps one at a time with ‹ › arrows, ending
    in a small-numbers check computed by the pipeline → "Show solution", right under Help with
    the same arrows, shows each step's math with this problem's numbers and its value.
  - Undefined blanks (0⁰, 0 ÷ 0) get their own message.
  - Blanks inside a Σ may hold expressions in its index (n − k), graded by trying k = 0…5. The
    pipeline checks every skeleton adds up to the answer.
  - Attempt tracking with try dots (D5); mastered = right within 2 tries; Help nudge after 3
    wrong tries.

**Next**
1. **Regenerate 3 samples with `family-v3`** (marbles-in-jars, hat-check-no-match,
   line-relative-order), one at a time, then review each on `/dev/preview/<slug>`. On 2026-10-21
   gemini-3.8-flash answered 503 (overloaded) and gemini-3.7-flash has no free daily quota for
   this key; a run now stops after the first overloaded target, and the request count follows
   Google's Pacific-time day.
2. **Design checkpoint D3 (Home):** options A path / B branching map / C dashboard are in
   `design/mockups/d3-home.html`, waiting for a choice; then milestone 9.
3. **Generate the other methods** (~48 families) in daily batches within the free quota, each
   reviewed before publishing.
4. **Milestones 7–8:** daily problem, "practice again", Progress page (heatmap, chart).
5. **Follow-ups** are tracked in [POLISH.md](POLISH.md), e.g. lazy-loading the Compute Engine
   bundle before the deploy.

## Roadmap: v1 and v2

**v1 (MVP, milestones 0–12): a live practice site**
- **Done:** playable problems; the answer-first flow with Help blanks; exact grading; the
  pipeline Gemini → verify → publish.
- **In progress:** methods, practice by method, saved progress, Σ notation.
- **Next:** the roadmap Home, visuals (incl. the card-deck grid), content runs, deploy.

**v2+ (post-MVP, details in §8)**
- Tutor chat ("Ask about this step").
- Login (Supabase) with progress synced across devices.
- Streaks and solved-per-difficulty.
- Weak spots, tutorials, "Fix my weak spots".
- User-uploaded problems (private first).
- ML: predict difficulty, recommend the next problem.

## Context
A LeetCode-style practice site for combinatorics and probability. Learners answer first and get
help only when they need it, so they find exactly where they overcount or undercount.
**The skill trained is choosing the right formula and what to plug in, not arithmetic.**

- **Input:** answers are math expressions typed in a Desmos-like MathLive field and graded by
  value, so any equivalent form counts.
- **Answer-first flow** (decided 2026-10-20, replacing the step player and the Guided/Free
  toggle):
  1. **Answer:** only the final answer box is shown (free mode).
  2. **Wrong answer:** targeted feedback for recognised mistakes ("That counts ordered picks…"),
     then the learner retries. A **Help** button is always visible.
  3. **Help:** the full skeleton on one line, e.g.
     $\binom{\square}{\square}\times\binom{\square}{\square}$. A group label sits under each
     part (juniors, seniors), and each slot shows a small hint (total, pick). The learner only
     fills in numbers.
  4. **Show solution:** offered after one wrong skeleton attempt. It shows the step-by-step
     explanation as read-only text, using the math-symbol step icons.
  - A problem counts as **solved** whenever the final answer is correct, with or without help.
    The help level is recorded on each attempt.
- **A visual** shows items being picked.
- **Practice again:** "New numbers" and "Try a variation".
- **Progress:** an attempt log, an activity heatmap and a daily attempts-vs-correct chart, all
  in localStorage.

**$0 hybrid content pipeline:** **generate → verify → publish**.
- **Generate:** the Gemini API free tier (Google AI Studio key in a gitignored `.env`) generates
  problem *templates* (variables + ranges + answer, skeleton and solution + Python checker). It runs behind a
  pluggable `Generator` interface.
- **Verify:** every template is verified by its brute-force checker (and simulation, where
  relevant) across several random variable settings. Passing families go to `content/`. Failing
  ones go to `needs_review/` with a report, for manual fixing in Claude Code sessions.
- **Publish:** builds a static bank with verified instances, about 50 templates → thousands of
  problems.

The site is fully static on Vercel, with no runtime AI calls or paid APIs. The MVP has no login.
Data shapes are Supabase-ready, and post-MVP features (streaks, weak spots, tutorials) are planned
into the schema now. This is a resume project, so clean code and the README matter.

---

## 1. Expressions (no hand-written parsers)

- **Storage format:** ASCII in a small, documented vocabulary: `C(n,k)`, `P(n,k)`, `n!`, `^`,
  `e`, `+ - * /`, parentheses, and variables. Variable names are a single letter, optionally
  with a digit (`n`, `k2`).
- **Python (sympy):**
  - Expressions are parsed with Python's `ast` against a whitelist (never `eval`'d), then built
    into sympy: `C`→`binomial`, `P`→`ff`, `n!`→`factorial`, `e`→`E`, `Sum`→`Sum`.
  - A custom LaTeX printer emits `\binom{}{}`, `\operatorname{P}(n,k)` and `\placeholder[id]{}`
    for skeleton slots.
- **Build precomputes instances:**
  - For each problem, the pipeline samples up to 100 valid variable assignments and evaluates
    every blank, slot and final answer per instance with sympy.
  - Values are stored as exact rationals (`"840"`, `"7/30"`), or as `{approx}` with 17
    significant digits when `e` is involved.
  - **So the browser never evaluates canonical expressions or constraints**: it only evaluates
    the user's input.
- **Browser (MathLive + Compute Engine):**
  - Input:
    - `<math-field>`: `/` makes a fraction, `^` an exponent, `!` a factorial.
    - `inlineShortcuts`: `choose` and `C(` → `\binom{#?}{#?}`; `P(` → `\operatorname{P}(#?,#?)`.
    - `e`; and a custom virtual keyboard for mobile.
  - Grading: user LaTeX → Compute Engine (with a custom `P`) → value → compared with the stored
    instance value. Exact comparison for rationals, relative tolerance `1e-9` for reals. Guards
    on huge `!`/`C`/`P`/`^`.
  - Help skeleton: the skeleton LaTeX has `\placeholder[slot]{}` prompts. Grading substitutes
    the prompt values into the skeleton and evaluates the result. Mismatched slots (versus the
    stored slot values) are flagged as a hint, but the verdict is decided by value, so `C(8,5)`
    is accepted.
  - **Spike result (milestone 1):** the Compute Engine evaluates binomials, factorials, a custom
    `P`, and fractions exactly, so mathjs is not needed. Decimal inputs are converted to exact
    fractions before comparison, so a rounded 0.2333 is not accepted as 7/30.
- **Accepted limitation:** grading by value accepts a coincidentally equal wrong formula. This
  is documented in the README.

## 2. Schemas

The Pydantic models (`pipeline/src/overcount/schema.py`) are the source of truth. They are
exported to `spec/*.schema.json`, and TS types are generated from those files.

### 2a. Authored/generated family (`content/families/<slug>/family.json` + `checker.py`)
```jsonc
{
  "family_id": "committee-mixed",
  "problems": [
    {
      "id": "committee-mixed",               // stable forever (Supabase keys)
      "variant_of": null,                    // case variant → "committee-mixed"
      "twist": null,                         // case variant → "at least one senior" (chip)
      "schema_version": 1,
      "origin": { "kind": "generated", "generator": "gemini", "model": "<from .env>", "prompt_version": "family-v1",
                  "target": { "topic": "counting/combinations", "context": "committees-seating", "difficulty": "easy" },
                  "inspired_by": null },     // or "authored" (hand-written in Claude Code)
      "title": "Robotics club team",
      "statement": "A club has {{J}} juniors and {{S}} seniors. In how many ways can a team of {{j}} juniors and {{s}} seniors be chosen?",
      "variables": {
        "J": { "min": 5, "max": 12, "default": 8 },
        "S": { "min": 4, "max": 10, "default": 6 },
        "j": { "min": 2, "max": 5,  "default": 3 },
        "s": { "min": 2, "max": 4,  "default": 2 }
                                             // non-integer: {"values": ["1/6","1/4","1/2"], "default": "1/6"}
      },
      "constraints": ["j < J", "s < S"],     // sympy relationals
      "difficulty": "easy",
      "tags": { "topics": ["counting/combinations"], "contexts": ["committees-seating"] },
      "answer": {
        "prompt": "Total number of teams",
        "expr": "C(J,j)*C(S,s)",
        "common_wrong": [                   // checked against free answers; each names a mistake
          { "expr": "P(J,j)*P(S,s)",  "mistake_tag": "order-confusion", "feedback": "That counts ordered picks. A team has no order." },
          { "expr": "C(J,j)+C(S,s)",  "mistake_tag": "add-vs-multiply", "feedback": "Adding counts teams of only juniors or only seniors…" },
          { "expr": "C(J+S,j+s)",     "mistake_tag": "overcount",       "feedback": "That counts every team of the right size, including the wrong mix…" }
        ],
        "skeleton": {                       // the Help view: one line, numbers only
          "expr": "C({a},{b})*C({c},{d})",
          "groups": [ { "label": "juniors", "slots": ["a", "b"] }, { "label": "seniors", "slots": ["c", "d"] } ],
          "slots": { "a": { "hint": "total", "answer": "J" }, "b": { "hint": "pick", "answer": "j" },
                     "c": { "hint": "total", "answer": "S" }, "d": { "hint": "pick", "answer": "s" } },
          "slot_mistakes": [                // optional: a wrong slot value that names a mistake
            { "slot": "a", "expr": "J+S", "mistake_tag": "overcount", "feedback": "That's everyone in the club. This part only picks from the juniors." }
          ]                                 // only checked for slots whose group value is wrong (C(8,5) = C(8,3) is never flagged)
        }
      },
      "solution": [                         // read-only, shown by "Show solution"
        { "kind": "choose",  "title": "Pick the juniors", "expr": "C(J,j)",
          "explanation": "Order doesn't matter on a team, so this is C({{J}}, {{j}})." },
        { "kind": "choose",  "title": "Pick the seniors", "expr": "C(S,s)", "explanation": "…" },
        { "kind": "combine", "title": "Combine", "expr": "C(J,j)*C(S,s)",
          "explanation": "Both choices happen together, so multiply (the product rule)." }
      ],
      "visual": { "kind": "pick", "pools": [ { "label": "juniors", "total": "J", "slot": "b" },
                                             { "label": "seniors", "total": "S", "slot": "d" } ] },
      "checker": "solve_root",               // fn in checker.py; null if the outcome space is infinite
      "simulator": null                      // e.g. "sim_root" (fn(rng, **vars) -> outcome); required for probability problems
    }
    // + 2–3 case variants
  ]
}
```

**Topic tags** (enum in `taxonomy.py`). `tags.topics[0]` is the problem's **primary topic**,
which places it on the roadmap.
- `counting/basics` (product/sum rule), `counting/permutations`, `counting/combinations`,
  `counting/stars-bars`, `counting/complement`, `counting/inclusion-exclusion`,
  `counting/symmetry-circular`
- `probability/basics`, `probability/independence`, `probability/expectation`,
  `probability/conditional-bayes`
- `distributions/binomial`, `distributions/hypergeometric`, `distributions/geometric`,
  `distributions/poisson`

**Context tags:** `cards-poker`, `dice`, `balls-urns`, `committees-seating`.

**Card problems** (context `cards-poker`, decided 2026-10-20):
- Every card problem sets `deck`. The default is `"standard"`: the usual 52-card deck with 13
  ranks and 4 suits.
- Standard-deck problems are **exempt from the "at least 5 number sets" gate**. Often only the
  hand size can vary, which leaves few sets. When a problem has fewer than 5 sets, the app
  **hides "New numbers"**.
- Variety comes from **case variants** instead (flush, full house, two pair, at least one ace…),
  offered through "Try a variation".
- `"custom"` decks (fewer ranks, extra suits) are allowed **only for Hard problems**, and the
  statement must describe the deck fully. The schema enforces the deck and difficulty rules;
  the prompt (`family-v2`) asks for the statement wording.

**Examples and visuals** (required on every problem)
- **Checker convention** (`checker.py`, names listed in `family.json` under `checker`):
  - `outcomes(**vars)`: every *candidate* outcome a beginner might write down. For a round
    table that's every ordering; for candy in bags, every way to put 0..n in each bag.
  - `counts(outcome, **vars) -> bool`: the rule. The answer is verified by counting candidates
    that pass (a fraction of all candidates for probabilities). With unequal chances, leave out
    `outcomes` and use a simulator.
  - `example(**vars)`: a hand-picked ✅ and ❌ outcome, plus optional `highlight` (positions),
    `pool` (subsets; a list or named groups such as juniors/seniors) and `captions` (one short
    label per piece, e.g. "president", or kids A, B, C).
  - `reason(outcome, **vars) -> str`: a one-line reason for any outcome, e.g. "two 6s" or "adds
    to 9, not 7". Used for every example, including "Show another example".
- **Visual** `{type, legend?}`: one of dice, coins, sequence, circle, subset, boxes, stars-bars,
  cards, path, matching. Each type fixes the outcome's shape (validated, at most 12 pieces), so
  the web draws it with one shared component instead of LLM-written SVG. `legend` is an optional
  short line such as "● = a cookie, | = a divider between kids".
- **Published per instance:** the hand-picked pair plus up to 4 more pairs sampled from the
  checker's own outcomes (seeded, so builds are reproducible). Each has its text form (e.g.
  "A=3, B=0, C=4") and reason. Every pair is checked: ✅ passes `counts`, ❌ doesn't, and both are
  real outcomes of that instance. Nothing about the answer or solution is included.
- **Wording rules** (prompt `family-v3`): plain words; describe one outcome concretely ("write the
  results as a list, like 6, 6, 1, 3, 2"); say whether order matters; never use a vague term
  like "sequence" or "arrangement" without an example.
- **Generation retry:** a reply missing `example` or `visual`, or failing the example check, is
  sent back with the error, up to 2 retries per target.

**Roadmap** (`content/roadmap.yaml`, exported into `index.json`): an ordered list of nodes
`{id, title, blurb, prereqs: [node ids], topic_tags: [...]}`. Each topic tag belongs to exactly
one node (validated at build).
1. Counting basics: basics, permutations, symmetry-circular
2. Combinations: combinations
3. Stars & bars: stars-bars
4. Complement: complement
5. Inclusion–exclusion: inclusion-exclusion
6. Probability basics: probability/basics, independence, expectation
7. Conditional: conditional-bayes
8. Distributions: all four distributions

`prereqs` is linear for now, but the field allows a DAG later.

**Mistake tags** (enum in `taxonomy.py`): `order-confusion`, `overcount`, `undercount`,
`add-vs-multiply`, `missed-complement`, `replacement-confusion`, `wrong-distribution`,
`independence-assumed`, `conditional-reversed`, `off-by-one`.
- Every `common_wrong` and `slot_mistakes` entry **must** have a tag (enforced by the schema now).

**Step kinds** (solution steps, shown with their math-symbol icon; see DESIGN.md D2): `choose` C,
`arrange` P, `combine` ×+, `cases` Σ, `inclusion-exclusion` ∪, `complement` 1−, `overcount` ÷,
`condition` A|B, `distribution` ∼.
- Tags power the post-MVP weak-spots features.

### 2b. Published bank (static, lazy-loaded)
- `web/public/bank/index.json` holds metadata for lists and filters: id, family_id, title,
  difficulty, tags, mistake_tags, variant_of, twist and instance_count.
- `web/public/bank/families/<slug>.json` holds the problems without checker code, plus
  `instances: [{ key, vars, values: { "answer": "840", "slot.a": "8", "slot.b": "3", ... } }]`.
- `data/bank/` holds the full build, with verification metadata.

### 2c. Attempt log (localStorage now, Supabase `attempts` table later; same shape)
```ts
type Attempt = {
  id: string;              // uuid v4, client-generated → becomes the PK
  user_id: string | null;  // null until login; backfilled on first sign-in, then bulk-inserted
  problem_id: string;
  family_id: string;
  instance_key: string;    // which number variant
  help_level: 0 | 1 | 2;   // 0 free answer, 1 used the Help skeleton, 2 saw the solution
  attempted_at: string;    // ISO UTC
  local_date: string;      // YYYY-MM-DD in the user's timezone (heatmap/streak bucket)
  correct: boolean;        // counts as "solved" at any help level
  answer: string;          // the submitted LaTeX (free answer) or filled skeleton
  mistake_tags: string[];  // tags recognised on this submission (logged now, used post-MVP)
  schema_version: 1;
};
```
- An *attempt* is one answer submission, whether a free answer or a filled skeleton.
  Submitting the same answer again for the same problem and numbers is ignored (not a new try).
- **Tries and status per problem:** tries = attempts on that problem. **Mastered** = the first
  correct answer came within 2 tries; **solved** = correct later than that. The attempt count is
  shown on the problem page and in progress lists.
- **Help nudge:** after 3 wrong tries the page suggests opening Help before trying again. It
  never blocks another answer.
- The record is stored under `localStorage["overcount.attempts.v1"]` behind a `ProgressStore`
  interface (`add`, `list({from,to})`), implemented by `LocalStorageProgressStore`. A future
  `SupabaseProgressStore` will be a drop-in replacement.
- Everything else (heatmap, chart, and post-MVP streaks, per-difficulty counts and weak spots)
  is **derived** from this log joined with `index.json`, so no other persisted state is needed.

## 3. Pipeline: generate → verify → publish

**Generate (`overcount generate`)**
- **`GeminiGenerator`** (a real implementation, using the `google-genai` SDK) implements
  `Generator.generate(target) -> FamilyDraft`. `FileGenerator` handles hand-authored folders.
- **Input:** `content/targets.yaml` lists the coverage plan: topic × context × difficulty, an
  optional inspiration text, and the number of variants.
- **Prompt:** a versioned prompt (`prompts/family-v1.md`) with the schema summary, rules (small
  ranges so brute force is fast, mistake tags, checker/simulator rules) and 2 golden families as
  few-shot examples.
- **Output:** structured JSON (`response_mime_type=application/json` + response schema) →
  `{family, checker_code}`.
- **Batching and limits:**
  - Targets run in batches (one request per family, covering the root and its variants).
  - A token-bucket limiter is set from `.env` (`GEMINI_RPM`, `GEMINI_RPD`).
  - A small hand-written retry loop handles 429 and 5xx with exponential backoff and jitter,
    and honours the server's retry delay. A 404 (model unavailable) stops the run at once.
  - When the daily quota is exhausted, the run stops cleanly and is resumable:
    `data/generation_log.jsonl` records each target's status, and done targets are skipped.
- **Config:**
  - `.env` holds `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_RPM` and `GEMINI_RPD`.
  - `.env.example` is committed, and `.env` is gitignored.
  - The model is config, not code, because free-tier models and quotas change.
- **Destination:** drafts land in `staging/<slug>/`.

**Verify (`overcount verify staging/`)** routes each family:
- Pass → `content/families/<slug>/`.
- Fail → `needs_review/<slug>/` + `REPORT.md` with the gate, instance, expected vs. got, and
  the traceback.
- **Fixing:** in a Claude Code session, run `overcount verify needs_review/<slug>`, then
  `overcount promote <slug>` once it passes.

**MVP gates**
1. **Schema:** Pydantic models plus taxonomy and mistake-tag enums. Every expression must parse
   with sympy, and placeholders, variables and slots must be defined. Constraints must be
   satisfiable (the sampler finds ≥ 20 valid instances).
2. **Brute-force checker:** counting the `outcomes` that pass `counts` on the default instance,
   the range corners and 10 random instances must equal sympy's value of the answer on every one.
3. **Example:** on the same instances, the ✅ outcome passes `counts`, the ❌ one doesn't, both are
   among `outcomes`, both fit the visual type, and `reason` gives a short line for each.
4. **Simulation:** required when `simulator` is set (all probability and distribution problems,
   and the only evidence for infinite outcome spaces such as geometric and Poisson). Monte Carlo
   on 2 instances, with the exact value inside the 99.9% CI.

**Sandbox (a safety requirement, not a gate):** generated checker code is untrusted.
- Before it runs, an AST allowlist permits imports of `itertools`, `fractions`, `math`, `random`,
  `functools` and `collections` only. It bans `open`, `exec`, `eval`, `__import__` and dunder
  attribute access.
- It runs in a subprocess (`python -I`) with a timeout and CPU/memory rlimits.

**Later gates (post-MVP):** skeleton-and-solution consistency with the answer, `common_wrong` ≠ correct
value, a checker-independence lint (no `math.comb` and similar), and a CE ↔ sympy cross-check in
CI. Until then, a vitest covers CE grading of the golden problems' canonical answers.

**Publish (`overcount build`)** samples and precomputes instances, then writes `data/bank/` and
`web/public/bank/`.
- Both outputs are committed, so Vercel only runs `vite build`.
- `overcount stats` prints the funnel (generated → passed → needs_review → promoted), coverage
  per tag and difficulty, and the total verified instances.

## 4. Tech stack & folder structure

- **Pipeline:** Python 3.14 (compatible with 3.12+), `uv`, `pydantic` v2, `sympy`, `typer`,
  `google-genai`, `python-dotenv`, `pyyaml`, `ruff`, `mypy`, `pytest`.
- **Web:** Vite + React + TS + Tailwind, `mathlive` + `@cortex-js/compute-engine` (no mathjs; see the
  spike result in §1), KaTeX for statements and explanations, Framer Motion, React Router, Recharts (line
  chart), a custom SVG heatmap, Vitest. Static deploy on Vercel.

```
overcount/
├── README.md                    # pitch, GIF, generate→verify→publish diagram, funnel stats, setup (.env), roadmap
├── AUTHORING.md                 # family format, checker/simulator rules, fixing needs_review in Claude Code
├── .env.example                 # GEMINI_API_KEY=, GEMINI_MODEL=, GEMINI_RPM=, GEMINI_RPD=
├── spec/                        # generated JSON Schemas
├── content/
│   ├── targets.yaml             # coverage plan for generation
│   └── families/<slug>/  family.json  checker.py
├── staging/                     # gitignored: fresh generator output
├── needs_review/<slug>/         # committed: family.json, checker.py, REPORT.md
├── pipeline/
│   ├── pyproject.toml
│   ├── src/overcount/
│   │   ├── schema.py  taxonomy.py
│   │   ├── expr.py              # sympy parse/evaluate/latex helpers
│   │   ├── instances.py         # constraint sampling + value precompute
│   │   ├── generate/            # base.py (Generator), gemini.py, files.py, ratelimit.py, prompts/
│   │   ├── verify/              # gates.py, sandbox.py, simulate.py, report.py
│   │   ├── publish.py           # build bank
│   │   └── cli.py               # generate | verify | promote | build | stats | new-family
│   └── tests/
├── data/  bank/  generation_log.jsonl
└── web/
    ├── src/
    │   ├── components/          # ProblemPage, AnswerBox, MathInput, HelpSkeleton, SolutionSteps, StepIcon,
    │   │                        # PracticeAgainBar, PickVisual, SlotsVisual, TagFilter, ActivityHeatmap, DailyChart
    │   ├── lib/                 # grade.ts, bank.ts (ProblemRepository), progress.ts (ProgressStore), stats.ts, daily.ts
    │   ├── pages/               # Home (roadmap + daily + mini heatmap), Topic, Practice, Problem, Progress
    │   └── types/               # generated
    └── public/bank/  index.json  families/*.json
```

## 5. Home page: NeetCode-style roadmap
- **Roadmap graph:** nodes drawn in learning order and joined by connector lines (custom SVG
  edges over a CSS grid, no graph library; vertical on mobile).
- **Each node card** shows the title and lists its **counting methods** (from
  `content/roadmap.yaml`), each with solved / total and a link to `/practice?method=…`. One
  taxonomy, one place: there are no `/topics` pages. Nodes without methods (the probability
  ones) link to their problems.
- **Rest of Home:** the daily problem card and the mini heatmap stay on Home. Practice (all
  problems with filters) stays as a separate page.

## 5b. Design direction & decision process

**Purpose first.** Overcount is a learning tool, so every visual choice must serve
understanding:
- One problem in focus, a clear step flow, readable math and an obvious "next" action.
- The picking visual and the feedback do the teaching.

**Personality:** light Overcooked-inspired touches, with no characters, logos or assets from
the game.
- Order-ticket problem cards and small ingredient-style step icons.
- Plain, calm correct feedback ("✓ Correct. That's 840."), with no "served" label.
- A warm palette (off-white background, cream cards, muted teal accent, soft terracotta, sage
  for correct, berry for wrong; see DESIGN.md D1).
- A pixel font (Pixelify Sans) only for the logo and small stat labels. All digits use
  Atkinson Hyperlegible, which is the readable font for everything else.
- Overall it should feel polished at LeetCode/Duolingo quality, calm and hand-designed: no
  generic gradients, glassmorphism or emoji-heavy UI.

**You make the visual decisions.** At each checkpoint below, I'll show 2–3 options as rendered
mockups in chat, give my recommendation and why, and **wait for your pick** before building.
Decisions are recorded in `DESIGN.md` (choice + rationale), which also makes a good README and
resume section.

| Checkpoint | When | Options shown |
|---|---|---|
| **D1: Palette & type** | before milestone 1 styling | 3 palettes built from your starting idea (one includes a dark-mode variant). 2–3 type pairings: body font + pixel font + how they sit next to KaTeX/MathLive math |
| **D2: Problem page** | before milestone 2 | Layouts, e.g. (a) single-column ticket with steps stacked, (b) two-pane with problem + visual left and steps right, (c) Duolingo-style one step at a time. Also step-icon style and feedback styling |
| **D3: Home & progress** | before milestone 9 | Roadmap composition (vertical path vs. zig-zag vs. grouped lanes), where the daily problem and mini heatmap sit, and heatmap/chart styling |

**Implementation rules** (independent of which options you pick):
- All colors, fonts, radii and shadows are tokens (`web/src/styles/tokens.css` → Tailwind
  theme). No hard-coded hex values in components, so a pick can be swapped in one file.
- D1 was decided before milestone 1, so milestone 1 already uses the final tokens.
- A vitest **contrast test** checks every text/background token pair against WCAG AA (4.5:1
  for body text, 3:1 for large text and UI borders and icons).
- `prefers-reduced-motion` is respected, all flows work from the keyboard, and feedback is never
  conveyed by color alone.

**Usability flags on the starting ideas** (I'll design the options around these):
1. **"Low-contrast" palette.** Low contrast is fine *between surfaces* (off-white vs. cream),
   but text and math must hit AA. A muted teal usually fails as text on cream, so each accent
   needs a darker "ink" shade for text and links and a lighter shade for fills.
2. **Sage vs. muted red.** Red/green color-blindness affects roughly 1 in 12 men. Two muted
   tones at similar lightness will look the same to them. Correct and wrong states always get
   an icon + word (✓ Correct / ✗ Not quite) and clearly different lightness, not hue alone.
3. **Terracotta next to muted red.** The two can be confused, so a decorative accent might
   read as an error. I'll keep terracotta for decoration only (ticket stubs, logo) and give
   "wrong" a clearly different hue or treatment.
4. **Pixel font for numbers.** Small pixel digits blur (1/7, 3/8, 5/6). Resolved in D1: digits
   are never drawn in the pixel font. A composite font renders them in Atkinson Hyperlegible at
   88%.
5. **Overcooked's time pressure.** It's the opposite of calm learning, so there are no countdown
   timers, urgency mechanics or celebration animations that delay the "Next" button.
6. **Ingredient icons.** These only help if they're consistent: one icon per step *kind*
   (choose, arrange, combine ×/+, divide out overcount, complement, condition, distribution),
   always paired with a text label. Decorative icons that vary per problem would add noise.

## 6. Git, GitHub & security
- **Project folder:** `~/Documents/personal projects/overcount`, with a private GitHub repo at
  `fsutedja/overcount`.
- **Repo:**
  - `git init -b main`, then `gh auth status`.
  - `gh repo create overcount --private --source=. --remote=origin`, then the first push
    after the security checks below.
- **Commits:** one commit (or a few) per milestone, with clear conventional messages
  (`feat(web): playable problem with MathLive grading`) and **no attribution lines**. Commit when
  a milestone is done; **push only after you approve it** each time.
- **Secrets:**
  - The only secret is `GEMINI_API_KEY`. It lives in the root `.env`, which is gitignored
    alongside `.env.*` except `.env.example`.
  - The key is read only by `pipeline/` (and post-MVP by the `web/api/tutor.ts` serverless
    function via `process.env`, configured in Vercel's encrypted env settings, never committed).
  - **Never** prefix secrets with `VITE_`, and never reference them in `web/src`. A CI step and
    an ESLint `no-restricted-syntax` rule fail on `import.meta.env` usages other than the
    allowlisted, non-secret `VITE_` vars (none in the MVP), and on any `GEMINI` string under
    `web/`.
  - `gitleaks` runs as a **pre-commit hook** (`.pre-commit-config.yaml`, installed with
    `pre-commit install`) and as a CI step.
- **Before the first push:** run `git check-ignore -v .env` (it must print the ignore rule),
  `git ls-files | grep -i env` (only `.env.example`), and a gitleaks scan of the full git
  history (it must report 0 findings).

## 7. MVP milestones (playable as early as possible; commit after each, push on approval)

0. ✅ **Repo setup:** move to the permanent folder, `git init`, `.gitignore`, `.env.example`,
   pre-commit + gitleaks, README stub, the security checks above, `gh repo create`, first push.
   - **Design checkpoint D1** (palette & type) follows; I wait for your pick. D2 comes before
     milestone 2 and D3 before milestone 9 (see §5b).
1. **Playable problem (day 1):** Vite app, one hand-written golden problem JSON with
   hand-computed instance values in `web/`, a `MathInput` with shortcuts, and Compute Engine
   grading of the final answer in Free mode, including the CE spike (passed; no mathjs needed).
   **Result: a real problem you can solve on screen.** ✅ Done.
2. ✅ **Answer-first player** (milestones 2 and 3 merged after the flow change):
   - Free answer box with targeted `common_wrong` feedback and retry.
   - Help: a one-line placeholder skeleton with group labels and slot hints, graded by value,
     with slot-mismatch and `slot_mistakes` feedback.
   - "Show solution" (offered after one wrong skeleton attempt): a read-only step list with
     math-symbol icons.
   - The two-pane layout, the final bonus number, and attempt records with `help_level` and
     mistake tags (stored in memory for now; `ProgressStore` comes in milestone 8).
4. ✅ **Pipeline core:** uv project, Pydantic schemas (web types hand-written, checked by the bank cross-check), sympy expressions,
   instance sampler, `build`. Three golden families authored in Claude Code (committee, ×-vs-+
   trap, circular-seating overcount; each with 1 variant) replace the hand-written web JSON.
5. ✅ **Verify:** sandbox + the 3 MVP gates, staging → content / needs_review routing with
   `REPORT.md`, `promote`, `stats`, and CI (pytest, vitest, `build --check`).
6. ✅ **Gemini generator:** `GeminiGenerator`, structured output, rate limiter, retries, resumable
   log, `.env`/`.env.example`, `targets.yaml`. First run of ~5 targets through
   generate → verify → publish.
7. **Practice + daily + practice again:** filters (topic, context, difficulty), date-seeded
   daily problem and instance, "New numbers" (hidden when a problem has fewer than 5 number
   sets, see card problems in §2a), and "Try a variation" (nudged after a reveal).
8. **Progress:** attempt logging via `ProgressStore` (attempt counts and mastered/solved are
   built early, see Status); a Progress page with attempts and mastered/solved per problem, a heatmap (one square
   per day, shaded by the number of distinct problems solved correctly that day) and a daily line
   chart (attempts vs. correct).
9. **Home roadmap:** the roadmap graph with each node's methods and solved / total (replacing the
   temporary `/practice` methods list), and the daily problem card + mini heatmap on Home.
10. **Visuals:** the outcome diagrams are already built (Status, §2a); what's left is binding
    them to the Help skeleton slots (highlight the pieces a slot counts), plus a **13×4 card-deck grid** (ranks × suits, relevant cards highlighted) for card problems.
    Style options are shown to you before building.
11. **Content runs:** generate by `targets.yaml` coverage (counting, inclusion–exclusion/
    complement, distributions, probability). Fix `needs_review` items in Claude Code sessions.
    Target ≈ 50 roots, ≥ 3 per topic tag, all contexts and difficulties.
    Every roadmap node needs ≥ 3 roots.
12. **README & deploy:** pipeline diagram, funnel and instance counts, GIF, setup guide, roadmap.
    Vercel deploy and a mobile/a11y pass.

## 8. Post-MVP (the data shape is ready now; build later)
- **Streak:** consecutive `local_date`s with ≥ 1 correct attempt (derived from the log). Shown on
  Home and Progress.
- **Solved per difficulty:** distinct correct `problem_id`s joined with `index.json`.
- **Weak spots:** counts of `mistake_tags` across attempts, as a profile panel.
- **Tutorials:** `content/lessons/<mistake_tag>.md`, one short lesson + worked example per tag,
  authored in advance.
- **"Fix my weak spots":** a practice set filtered by the problems whose `mistake_tags` include
  the user's top tags (already in `index.json`).
- **Supabase:** auth (email + Google), an `attempts` table with the same shape, and a
  `SupabaseProgressStore`. On first login, backfill `user_id` and bulk-insert local attempts.
- **"Ask about this step" tutor chat** (replaces the earlier "personalized explanations" idea):
  - **UI:** a small collapsible chat panel on the problem page, next to the current step. The
    user types only their question.
  - **Request:** the client sends *ids*, not text: `{problem_id, instance_key, step_id,
    blank_id, user_answer_latex, mistake_tag?, question}`. The serverless function
    (`web/api/tutor.ts`, Vercel) looks up the statement, the step template, the correct answer
    and the explanation from the bundled bank by id. This means a modified client can't inject
    fake "context". Only `question` and `user_answer_latex` are free text.
  - **Gemini call:** made server-side with `process.env.GEMINI_API_KEY` (never `VITE_`, never
    in `web/src`), using the same `.env` var names as the pipeline.
  - **System prompt:** answer in 2–3 sentences; explain the concept; give a hint before ever
    revealing the answer, and only reveal it if the user asks again; stay on combinatorics and
    probability and politely decline anything else. The user's text is wrapped in delimiters and
    treated as data, not instructions. Output is capped by `maxOutputTokens`.
  - **Input validation:** `zod` schema; the question is limited to ≤ 300 characters and the
    answer to ≤ 200; ids must exist in the bank; otherwise the request is rejected with 400.
  - **Rate limits:**
    - A per-user daily cap of 10 questions, keyed on the Supabase user id once login exists and
      on the hashed IP until then.
    - A global daily cap set below the free-tier quota (env `TUTOR_GLOBAL_DAILY_CAP`).
    - Vercel functions are stateless, so the counters live in **Upstash Redis** (free tier,
      via the Vercel Marketplace) or a Supabase table once auth exists.
  - **Fallback:** on a cap hit, a Gemini 429 or an error, the panel shows "Tutor is resting —
    try the hints or the tutorial for this mistake," with direct links to the step hints and the
    `lessons/<mistake_tag>` tutorial.
  - **Privacy note** in the panel: questions are sent to Google's Gemini API, and free-tier
    inputs may be used by Google to improve its products. So: "don't include personal info."
  - **Data shape now:** nothing new is needed. `problem_id`, `instance_key`, step and blank ids
    and `mistake_tags` already exist. A `tutor_messages` table can come later if you want
    history.
- **Later gates** from §3, and MATH-dataset inspiration ingest feeding `targets.yaml`.

## Verification
- `pytest`: sympy expression helpers (C, P, !, e, fractions), sampler, each gate with a
  deliberately broken fixture family, sandbox (timeout, banned import, banned builtin), and the
  generator with a mocked Gemini client (structured parse, 429 → backoff → success, quota stop
  → resume).
- Security: a commit containing a fake `AIza…` key is blocked by the pre-commit hook. The
  gitleaks history scan is clean before every push. The CI grep finds no secrets or `GEMINI`
  under `web/`, and `dist/` contains no key.
- `pytest` (pipeline): `roadmap.yaml` validation (each topic tag in exactly one node).
- `vitest`: roadmap progress derivation (roots only, primary topic); `grade.ts` on the golden problems (equivalent forms, `e` tolerance, guards),
  `stats.ts` (heatmap buckets, line-chart series, local-date bucketing across midnight), and
  `daily.ts` determinism.
- End to end: `overcount generate --limit 3 && overcount verify staging/ && overcount build &&
  overcount stats`, then hand-check one `needs_review` report.
- In the browser pane:
  - Solve a golden problem at each help level: free (the `choose` and `C(` shortcuts,
    `P(8,3)/3!` vs `C(8,3)`, a recognised mistake), Help skeleton (correct, a swapped
    `C(8,5)`, a wrong slot flagged), and Show solution.
  - "New numbers", and "Try a variation" after a reveal.
  - Make a few right and wrong attempts, then confirm the heatmap and line chart update and
    survive a reload.
  - Home roadmap: a node's progress bar moves after a correct answer, its link opens the topic
    page, and the layout works at phone width.
  - Design: the contrast test passes, and correct and wrong states read correctly in grayscale
    (color-blind proxy). With reduced motion on, nothing animates, and a full problem can be
    solved by keyboard only.
