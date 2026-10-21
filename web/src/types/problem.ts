// The shape of web/public/bank/, written by the pipeline (pipeline/src/overcount/publish.py).
// A vitest checks the committed bank against these types' required fields.
// Text fields may contain {{var}} placeholders, filled from the instance.

/** An exact rational ("840", "7/30") or, for answers involving e, a decimal approximation. */
export type StoredValue = { type: 'rational'; exact: string } | { type: 'real'; approx: number }

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
 * One labelled part of the Help skeleton, e.g. C([a], [b]) labelled "juniors".
 * `display` is shown to the learner; `latex` is what gets graded. Both use [slot] markers.
 */
export interface SkeletonGroup {
  label: string
  display: string
  latex: string
}

export interface Skeleton {
  /** Groups joined by operators: group, op, group, op, group… */
  parts: ({ group: SkeletonGroup } | { op: { display: string; latex: string } })[]
  /** Small hint shown inside each empty slot. */
  slots: Record<string, { hint: string }>
  slot_mistakes: (CommonWrong & { slot: string })[]
}

export interface SolutionStep {
  kind: StepKind
  title: string
  latex: string
  explanation: string
}

/** One concrete set of numbers for a template, with every answer precomputed by the pipeline. */
export interface Instance {
  key: string
  vars: Record<string, string>
  /** "answer" plus "slot.<id>" for each skeleton slot. */
  values: { answer: StoredValue } & Record<string, StoredValue>
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
