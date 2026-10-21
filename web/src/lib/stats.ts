import type { Attempt } from './attempts'
import { localDate } from './attempts'
import { problemProgress, type ProblemStatus } from './progress'

const addDays = (date: Date, days: number) => new Date(date.getFullYear(), date.getMonth(), date.getDate() + days)

/** Distinct problems solved on each local day. */
export function solvedPerDay(attempts: readonly Attempt[]): Map<string, number> {
  const perDay = new Map<string, Set<string>>()
  for (const a of attempts) {
    if (a.correct) perDay.set(a.local_date, (perDay.get(a.local_date) ?? new Set()).add(a.problem_id))
  }
  return new Map([...perDay].map(([day, ids]) => [day, ids.size]))
}

/** Longest run of consecutive days with at least one problem solved. */
export function bestStreak(attempts: readonly Attempt[]): number {
  const days = [...solvedPerDay(attempts).keys()].sort()
  let best = 0
  let run = 0
  let previous: string | null = null
  for (const day of days) {
    run = previous !== null && localDate(addDays(new Date(`${previous}T12:00:00`), 1)) === day ? run + 1 : 1
    best = Math.max(best, run)
    previous = day
  }
  return best
}

export interface ProblemRow {
  id: string
  status: ProblemStatus
  tries: boolean[]
}

/** Each problem's status and tries, for the Problems tab and the headline numbers. */
export function problemRows(attempts: readonly Attempt[], problemIds: string[]): ProblemRow[] {
  return problemIds.map((id) => ({ id, ...problemProgress(attempts, id) }))
}

/** Tries and right tries per day over the last `days` days, oldest first. */
export function triesPerDay(attempts: readonly Attempt[], today: Date, days = 30) {
  const tries = new Map<string, { tries: number; right: number }>()
  for (const a of attempts) {
    const day = tries.get(a.local_date) ?? { tries: 0, right: 0 }
    day.tries++
    if (a.correct) day.right++
    tries.set(a.local_date, day)
  }
  return Array.from({ length: days }, (_, i) => {
    const date = localDate(addDays(today, i - days + 1))
    return { date, ...(tries.get(date) ?? { tries: 0, right: 0 }) }
  })
}

/** Columns a month label needs before the next one starts. */
const MIN_LABEL_GAP = 3

export interface HeatCell {
  date: string
  /** Distinct problems solved that day. */
  count: number
  /** 0–3 shade (3 = 3 or more). */
  level: number
  /** False for days after today in the last week's column. */
  inRange: boolean
}

/**
 * GitHub-style calendar: `weeks` columns of 7 days (Sunday first), ending with the week that
 * holds today. Also returns where each month label goes (the first column starting in it).
 */
export function calendar(attempts: readonly Attempt[], today: Date, weeks = 52) {
  const perDay = solvedPerDay(attempts)
  const lastSunday = addDays(today, -today.getDay())
  const start = addDays(lastSunday, -7 * (weeks - 1))
  const columns: HeatCell[][] = []
  const months: { column: number; label: string }[] = []
  for (let w = 0; w < weeks; w++) {
    const column: HeatCell[] = []
    for (let d = 0; d < 7; d++) {
      const day = addDays(start, w * 7 + d)
      const date = localDate(day)
      const count = perDay.get(date) ?? 0
      column.push({ date, count, level: Math.min(3, count), inRange: day <= today })
    }
    const first = addDays(start, w * 7)
    const previous = addDays(first, -7)
    if (w === 0 || first.getMonth() !== previous.getMonth()) {
      months.push({ column: w, label: first.toLocaleDateString('en-GB', { month: 'short' }) })
    }
    columns.push(column)
  }
  // Like GitHub, drop a month label that would collide with the next one (a month that only
  // has a column or two at the start of the year).
  const spaced = months.filter((m, i) => i === months.length - 1 || months[i + 1].column - m.column >= MIN_LABEL_GAP)
  const total = columns.flat().reduce((sum, cell) => sum + (cell.inRange ? cell.count : 0), 0)
  return { columns, months: spaced, total }
}
