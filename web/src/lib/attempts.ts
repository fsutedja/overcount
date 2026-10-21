import { progressStore } from './progress'
import type { MistakeTag } from '../types/problem'

/** 0 = free answer, 1 = used the Help skeleton, 2 = saw the solution. */
export type HelpLevel = 0 | 1 | 2

/** One answer submission. Same shape as the future Supabase `attempts` table (PLAN.md §2c). */
export interface Attempt {
  id: string
  user_id: string | null
  problem_id: string
  family_id: string
  instance_key: string
  help_level: HelpLevel
  attempted_at: string
  local_date: string
  correct: boolean
  /** The submitted LaTeX (free answer) or the filled-in skeleton. */
  answer: string
  mistake_tags: MistakeTag[]
  schema_version: 1
}

/** YYYY-MM-DD in the learner's own timezone, used to bucket the heatmap and streaks. */
export function localDate(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function createAttempt(
  fields: Pick<
    Attempt,
    'problem_id' | 'family_id' | 'instance_key' | 'help_level' | 'correct' | 'answer' | 'mistake_tags'
  >,
  now = new Date(),
): Attempt {
  return {
    id: crypto.randomUUID(),
    user_id: null,
    attempted_at: now.toISOString(),
    local_date: localDate(now),
    schema_version: 1,
    ...fields,
  }
}

/** Whitespace doesn't make an answer different. */
const sameAnswer = (a: string, b: string) => a.replace(/\s+/g, '') === b.replace(/\s+/g, '')

/**
 * Saves an attempt, unless it repeats an answer already submitted for the same problem and
 * numbers (that's not a new try). Returns whether it was saved.
 */
export function recordAttempt(attempt: Attempt): boolean {
  const repeat = progressStore
    .list()
    .some(
      (a) =>
        a.problem_id === attempt.problem_id &&
        a.instance_key === attempt.instance_key &&
        sameAnswer(a.answer ?? '', attempt.answer),
    )
  if (repeat) return false
  progressStore.add(attempt)
  return true
}

export function recordedAttempts(): readonly Attempt[] {
  return progressStore.list()
}
