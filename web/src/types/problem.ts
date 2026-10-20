// Hand-written for milestone 1. From milestone 4 these types are generated from the
// pipeline's Pydantic schema (spec/problem.schema.json) so the web app and pipeline can't drift.

/** An exact rational ("840", "7/30") or, for answers involving e, a decimal approximation. */
export type StoredValue = { type: 'rational'; exact: string } | { type: 'real'; approx: number }

export type Difficulty = 'easy' | 'medium' | 'hard'

/** One concrete set of numbers for a template, with every answer precomputed by the pipeline. */
export interface Instance {
  key: string
  vars: Record<string, string>
  values: { final: StoredValue } & Record<string, StoredValue>
}

export interface Problem {
  id: string
  family_id: string
  title: string
  /** Markdown with {{var}} placeholders filled from the instance. */
  statement: string
  difficulty: Difficulty
  tags: { topics: string[]; contexts: string[] }
  final: {
    prompt: string
    /** Canonical expression in the storage grammar, with {{var}} placeholders. */
    answer: string
  }
  instances: Instance[]
}
