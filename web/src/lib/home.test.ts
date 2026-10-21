import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { BankIndex } from '../types/problem'
import { createAttempt } from './attempts'
import { currentNode, dailyProblem, dayStreak, heatmap, mapRows, nodeTally } from './home'

const index = JSON.parse(readFileSync(new URL('../../public/bank/index.json', import.meta.url), 'utf8')) as BankIndex

const solvedOn = (problem_id: string, day: string, correct = true) =>
  createAttempt(
    { problem_id, family_id: problem_id, instance_key: 'k', help_level: 0, correct, answer: day + problem_id, mistake_tags: [] },
    new Date(`${day}T12:00:00`),
  )

describe('home', () => {
  it('places each stop one row below the stops it follows', () => {
    const rows = mapRows(index.roadmap)
    expect(rows.get('counting-basics')).toBe(0)
    expect(rows.get('combinations')).toBe(1)
    expect([rows.get('stars-and-bars'), rows.get('complement')]).toEqual([2, 2])
    expect(rows.get('inclusion-exclusion')).toBe(3)
  })

  it('picks the same daily problem all day, from the root problems', () => {
    const morning = dailyProblem(index, new Date('2026-10-21T08:00:00'))
    expect(dailyProblem(index, new Date('2026-10-21T23:00:00'))).toEqual(morning)
    expect(morning?.variant_of).toBeNull()
  })

  it('counts solved problems per stop and finds the stop to work on', () => {
    const first = index.roadmap[0]
    expect(nodeTally(index, first, new Set()).done).toBe(0)
    expect(currentNode(index, new Set())).toBe(first.id)
    const allFirst = new Set(index.problems.filter((p) => first.topics.includes(p.tags.topics[0])).map((p) => p.id))
    expect(currentNode(index, allFirst)).not.toBe(first.id)
  })

  it('counts a streak up to today, or up to yesterday if nothing is solved yet today', () => {
    const attempts = [solvedOn('a', '2026-10-19'), solvedOn('b', '2026-10-20'), solvedOn('c', '2026-10-17')]
    expect(dayStreak(attempts, new Date('2026-10-21T09:00:00'))).toBe(2)
    expect(dayStreak([...attempts, solvedOn('d', '2026-10-21')], new Date('2026-10-21T09:00:00'))).toBe(3)
    expect(dayStreak([solvedOn('a', '2026-10-21', false)], new Date('2026-10-21T09:00:00'))).toBe(0)
  })

  it('shades days by distinct problems solved, capped at 3', () => {
    const attempts = ['a', 'b', 'c', 'd'].map((id) => solvedOn(id, '2026-10-21')).concat(solvedOn('a', '2026-10-20'))
    const cells = heatmap(attempts, new Date('2026-10-21T09:00:00'), 3)
    expect(cells).toEqual([
      { date: '2026-10-19', level: 0 },
      { date: '2026-10-20', level: 1 },
      { date: '2026-10-21', level: 3 },
    ])
  })
})
