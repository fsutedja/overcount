import { describe, expect, it } from 'vitest'
import { createAttempt } from './attempts'
import { LocalStorageProgressStore, problemProgress, solvedProblemIds } from './progress'

function memoryStorage() {
  const data = new Map<string, string>()
  return { getItem: (key: string) => data.get(key) ?? null, setItem: (key: string, value: string) => void data.set(key, value) }
}

let clock = 0
const attempt = (problem_id: string, correct: boolean) =>
  createAttempt(
    { problem_id, family_id: problem_id, instance_key: 'n=4', help_level: 0, correct, answer: 'x', mistake_tags: [] },
    new Date(Date.UTC(2026, 9, 21, 0, 0, clock++)),
  )

describe('LocalStorageProgressStore', () => {
  it('saves attempts and reads them back', () => {
    const store = new LocalStorageProgressStore(memoryStorage())
    store.add(attempt('round-table', false))
    store.add(attempt('round-table', true))
    expect(store.list().map((a) => a.correct)).toEqual([false, true])
  })

  it('treats missing or corrupt storage as no progress', () => {
    expect(new LocalStorageProgressStore(null).list()).toEqual([])
    const broken = memoryStorage()
    broken.setItem('overcount.attempts.v1', '{not json')
    expect(new LocalStorageProgressStore(broken).list()).toEqual([])
  })
})

describe('solvedProblemIds', () => {
  it('counts a problem as solved after any correct attempt', () => {
    const solved = solvedProblemIds([attempt('a', false), attempt('b', true), attempt('a', true), attempt('c', false)])
    expect([...solved].sort()).toEqual(['a', 'b'])
  })
})

describe('problemProgress', () => {
  const statusAfter = (...results: boolean[]) => problemProgress(results.map((r) => attempt('p', r)), 'p')

  it('is new before any try', () => {
    expect(statusAfter()).toEqual({ tries: [], wrong: 0, status: 'new' })
  })

  it('masters a problem solved in one or two tries', () => {
    expect(statusAfter(true)).toMatchObject({ tries: [true], status: 'mastered' })
    expect(statusAfter(false, true)).toMatchObject({ tries: [false, true], status: 'mastered' })
  })

  it('marks a later right answer as solved, and stops the dots there', () => {
    expect(statusAfter(false, false, true, false)).toEqual({ tries: [false, false, true], wrong: 2, status: 'solved' })
  })

  it('counts wrong tries while unsolved, for the Help nudge', () => {
    expect(statusAfter(false, false, false)).toEqual({ tries: [false, false, false], wrong: 3, status: 'tried' })
  })

  it('only counts the asked problem', () => {
    expect(problemProgress([attempt('other', true)], 'p').status).toBe('new')
  })
})
