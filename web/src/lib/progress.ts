import type { Attempt } from './attempts'

/**
 * Where attempts are saved. localStorage for now; a Supabase store with the same interface
 * replaces it once login exists (PLAN.md §2c), so nothing else has to change.
 */
export interface ProgressStore {
  add(attempt: Attempt): void
  list(): Attempt[]
}

const STORAGE_KEY = 'overcount.attempts.v1'

export class LocalStorageProgressStore implements ProgressStore {
  private readonly storage: Pick<Storage, 'getItem' | 'setItem'> | null

  constructor(storage: Pick<Storage, 'getItem' | 'setItem'> | null = safeLocalStorage()) {
    this.storage = storage
  }

  list(): Attempt[] {
    try {
      const raw = this.storage?.getItem(STORAGE_KEY)
      const parsed: unknown = raw ? JSON.parse(raw) : []
      return Array.isArray(parsed) ? (parsed as Attempt[]) : []
    } catch {
      return []
    }
  }

  add(attempt: Attempt): void {
    try {
      this.storage?.setItem(STORAGE_KEY, JSON.stringify([...this.list(), attempt]))
    } catch {
      // Storage can be full or blocked (private mode); progress just isn't saved this time.
    }
  }
}

function safeLocalStorage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage
  } catch {
    return null
  }
}

export const progressStore: ProgressStore = new LocalStorageProgressStore()

/** Problems with at least one correct attempt, at any help level. */
export function solvedProblemIds(attempts: readonly Attempt[]): Set<string> {
  return new Set(attempts.filter((a) => a.correct).map((a) => a.problem_id))
}

export type ProblemStatus = 'new' | 'tried' | 'solved' | 'mastered'

export interface ProblemProgress {
  /** Each try in order, right or wrong, up to and including the first right one. */
  tries: boolean[]
  /** Wrong tries before the first right one (or so far, if not solved yet). */
  wrong: number
  /** Mastered = right within 2 tries; solved = right later; tried = no right answer yet. */
  status: ProblemStatus
}

/** One problem's tries and status, from the attempt log (oldest first). */
export function problemProgress(attempts: readonly Attempt[], problemId: string): ProblemProgress {
  const mine = attempts
    .filter((a) => a.problem_id === problemId)
    .sort((a, b) => a.attempted_at.localeCompare(b.attempted_at))
  const firstRight = mine.findIndex((a) => a.correct)
  const tries = (firstRight === -1 ? mine : mine.slice(0, firstRight + 1)).map((a) => a.correct)
  const wrong = tries.filter((right) => !right).length
  const status: ProblemStatus =
    firstRight === -1 ? (mine.length ? 'tried' : 'new') : firstRight < 2 ? 'mastered' : 'solved'
  return { tries, wrong, status }
}

/** After this many wrong tries, the page suggests opening Help (it never blocks answering). */
export const NUDGE_AFTER_WRONG = 3
