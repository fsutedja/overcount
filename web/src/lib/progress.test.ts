import { describe, expect, it } from 'vitest'
import { createAttempt } from './attempts'
import { LocalStorageProgressStore, solvedProblemIds } from './progress'

function memoryStorage() {
  const data = new Map<string, string>()
  return { getItem: (key: string) => data.get(key) ?? null, setItem: (key: string, value: string) => void data.set(key, value) }
}

const attempt = (problem_id: string, correct: boolean) =>
  createAttempt({ problem_id, family_id: problem_id, instance_key: 'n=4', help_level: 0, correct, mistake_tags: [] })

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
