// The shape of web/public/bank/, written by the pipeline (pipeline/src/overcount/publish.py).
// A vitest checks the committed bank against these types' required fields.
// Text fields may contain {{var}} placeholders, filled from the instance.

/** An exact rational ("840", "7/30") or, for answers involving e, a decimal approximation. */
export type StoredValue =
  | { type: 'rational'; exact: string }
  | { type: 'real'; approx: number }
  /** A blank inside a Σ whose answer uses the index, e.g. "5 - k" (only for skeleton slots). */
  | { type: 'indexed'; latex: string; index: string }

export type Difficulty = 'easy' | 'medium' | 'hard'

/** Counting or Probability, derived by the pipeline from the primary topic. */
export type Kind = 'counting' | 'probability'

export interface Tags {
  topics: string[]
  contexts: string[]
  /** Counting techniques the problem drills (pipeline/src/overcount/taxonomy.py). */
  methods: string[]
}

/** Solution step kinds, each shown with its math-symbol icon (see DESIGN.md, D2). */
export type StepKind =
  | 'choose'
  | 'arrange'
  | 'combine'
  | 'cases'
  | 'inclusion-exclusion'
  | 'complement'
  | 'overcount'
  | 'condition'
  | 'distribution'

export type MistakeTag =
  | 'order-confusion'
  | 'overcount'
  | 'undercount'
  | 'add-vs-multiply'
  | 'missed-complement'
  | 'replacement-confusion'
  | 'wrong-distribution'
  | 'independence-assumed'
  | 'conditional-reversed'
  | 'off-by-one'

/** A predictable wrong answer, recognised by value, with feedback that names the mistake. */
export interface CommonWrong {
  latex: string
  feedback: string
  mistake_tag: MistakeTag
}

/**
 * One labelled part of the Help skeleton, e.g. C([a], [b]) labelled "juniors". `latex` is both
 * rendered (each [slot] becomes an empty box) and graded (each [slot] gets the learner's number).
 */
export interface SkeletonGroup {
  label: string
  latex: string
}

export interface Skeleton {
  /** Groups joined by operators: group, op, group, op, group… */
  parts: ({ group: SkeletonGroup } | { op: { latex: string } })[]
  /** Blank ids, in order. Blanks are empty boxes; the group labels say what each part counts. */
  slots: string[]
  slot_mistakes: (CommonWrong & { slot: string })[]
}

export interface SolutionStep {
  kind: StepKind
  title: string
  latex: string
  explanation: string
}

/** Diagram types for "one outcome" (pipeline/src/overcount/visual.py). */
export type VisualType =
  | 'dice'
  | 'coins'
  | 'sequence'
  | 'circle'
  | 'subset'
  | 'boxes'
  | 'stars-bars'
  | 'cards'
  | 'path'
  | 'matching'

/** An outcome as plain data: die faces, labels, counts, cards like "KH", path steps "R"/"U". */
export type Outcome = (number | string)[]

/** One outcome as shown in an example, with its text form and a one-line reason. */
export interface ExampleOutcome {
  outcome: Outcome
  text: string
  reason: string
  /** Positions to highlight in the diagram (e.g. where the 6s are). */
  highlight: number[]
}

/** One instance's examples, computed and checked by the pipeline. */
export interface InstanceExample {
  /** ✅/❌ pairs: the first is hand-picked, the rest feed "Show another example". */
  pairs: { yes: ExampleOutcome; no: ExampleOutcome }[]
  /** Subset visuals: everything that could be chosen, either one list or named groups. */
  pool?: string[] | Record<string, string[]>
  /** One short label per piece, e.g. "president", or bags A, B, C. */
  captions?: string[]
}

/** One concrete set of numbers for a template, with every answer precomputed by the pipeline. */
export interface Instance {
  key: string
  vars: Record<string, string>
  /** "answer" plus "slot.<id>" for each skeleton slot. */
  values: { answer: StoredValue } & Record<string, StoredValue>
  example: InstanceExample
}

export interface Problem {
  id: string
  family_id: string
  variant_of: string | null
  /** How a variant differs, shown as a chip, e.g. "one junior is captain". */
  twist: string | null
  title: string
  statement: string
  difficulty: Difficulty
  kind: Kind
  tags: Tags
  answer: {
    prompt: string
    latex: string
    common_wrong: CommonWrong[]
    skeleton: Skeleton
  }
  solution: SolutionStep[]
  /** How one outcome is drawn; `legend` explains the pieces, e.g. "★ = a candy". */
  visual: { type: VisualType; legend?: string }
  instances: Instance[]
}

export interface Family {
  family_id: string
  problems: Problem[]
}

/** One row of web/public/bank/index.json, used for lists and filters. */
export interface ProblemSummary {
  id: string
  family_id: string
  variant_of: string | null
  twist: string | null
  title: string
  difficulty: Difficulty
  kind: Kind
  tags: Tags
  mistake_tags: MistakeTag[]
  instance_count: number
}

export interface MethodInfo {
  id: string
  name: string
  blurb: string
}

/** A stop on the learning path, owning some topics and counting methods (content/roadmap.yaml). */
export interface RoadmapNode {
  id: string
  title: string
  blurb: string
  topics: string[]
  methods: MethodInfo[]
}

export interface BankIndex {
  schema_version: 1
  roadmap: RoadmapNode[]
  problems: ProblemSummary[]
}

/** One formula in a method lesson: rendered LaTeX and when it applies. */
export interface LessonFormula {
  id: string
  latex: string
  when: string
}

/** A method's "How it works" lesson (content/methods.yaml). Text marks math with $…$. */
export interface Lesson {
  name: string
  summary: string
  how: string[]
  formulas: LessonFormula[]
  example: string
  trap: string
}

export interface Lessons {
  schema_version: 1
  methods: Record<string, Lesson>
}
