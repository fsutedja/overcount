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
