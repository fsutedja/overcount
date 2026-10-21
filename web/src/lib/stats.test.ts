import { describe, expect, it } from 'vitest'
import { createAttempt } from './attempts'
import { bestStreak, calendar, problemRows, triesPerDay } from './stats'

const attempt = (problem_id: string, day: string, correct: boolean, n = 0) =>
  createAttempt(
    { problem_id, family_id: problem_id, instance_key: 'k', help_level: 0, correct, answer: `${problem_id}${day}${n}`, mistake_tags: [] },
    new Date(`${day}T12:0${n}:00`),
  )

const today = new Date('2026-10-21T15:00:00') // a Wednesday

describe('stats', () => {
  it('finds the longest run of days with something solved', () => {
    const days = ['2026-10-01', '2026-10-02', '2026-10-03', '2026-10-10', '2026-10-11']
    expect(bestStreak(days.map((d) => attempt('a', d, true)))).toBe(3)
    expect(bestStreak([attempt('a', '2026-10-01', false)])).toBe(0)
  })

  it('counts tries and right tries per day, oldest first', () => {
    const attempts = [attempt('a', '2026-10-21', false, 1), attempt('a', '2026-10-21', true, 2), attempt('b', '2026-10-20', true)]
    expect(triesPerDay(attempts, today, 3)).toEqual([
      { date: '2026-10-19', tries: 0, right: 0 },
      { date: '2026-10-20', tries: 1, right: 1 },
      { date: '2026-10-21', tries: 2, right: 1 },
    ])
  })

  it('lays the calendar out in Sunday-first weeks ending with this week', () => {
    const { columns, months, total } = calendar([attempt('a', '2026-10-21', true), attempt('b', '2026-10-21', true)], today, 4)
    expect(columns).toHaveLength(4)
    expect(columns[3][0].date).toBe('2026-10-18') // Sunday of this week
    expect(columns[3][3]).toMatchObject({ date: '2026-10-21', count: 2, level: 2, inRange: true })
    expect(columns[3][4].inRange).toBe(false) // Thursday hasn't happened yet
    // Starts on Sunday 27 Sep; "Sept" has one column before October starts, so like GitHub only
    // "Oct" is labelled.
    expect(months).toEqual([{ column: 1, label: 'Oct' }])
    expect(total).toBe(2)
  })

  it('gives each problem its status and tries', () => {
    const rows = problemRows([attempt('a', '2026-10-21', false, 1), attempt('a', '2026-10-21', true, 2)], ['a', 'b'])
    expect(rows).toEqual([
      { id: 'a', status: 'mastered', tries: [false, true], wrong: 1 },
      { id: 'b', status: 'new', tries: [], wrong: 0 },
    ])
  })
})
