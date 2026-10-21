import type { Attempt } from './attempts'
import { localDate } from './attempts'
import type { BankIndex, ProblemSummary, RoadmapNode } from '../types/problem'

/** Solved / total for a set of problems. */
export interface Tally {
  done: number
  total: number
}

const tally = (problems: ProblemSummary[], solved: ReadonlySet<string>): Tally => ({
  done: problems.filter((p) => solved.has(p.id)).length,
  total: problems.length,
})

/** Problems that belong to a roadmap stop (by their primary topic). */
export const nodeProblems = (index: BankIndex, node: RoadmapNode) =>
  index.problems.filter((p) => node.topics.includes(p.tags.topics[0]))

export const nodeTally = (index: BankIndex, node: RoadmapNode, solved: ReadonlySet<string>) =>
  tally(nodeProblems(index, node), solved)

export const methodTally = (index: BankIndex, method: string, solved: ReadonlySet<string>) =>
  tally(
    index.problems.filter((p) => p.tags.methods.includes(method)),
    solved,
  )

/** The stop to work on next: the first one with problems that aren't all solved. */
export function currentNode(index: BankIndex, solved: ReadonlySet<string>): string | null {
  const open = index.roadmap.find((node) => {
    const { done, total } = nodeTally(index, node, solved)
    return total > 0 && done < total
  })
  return open?.id ?? null
}

/** Row of each stop on the map: one more than the deepest stop it comes after. */
export function mapRows(nodes: RoadmapNode[]): Map<string, number> {
  const rows = new Map<string, number>()
  for (const node of nodes) {
    rows.set(node.id, node.after.length ? Math.max(...node.after.map((id) => rows.get(id) ?? 0)) + 1 : 0)
  }
  return rows
}

/** A small, stable hash so the same date always picks the same problem. */
function hash(text: string): number {
  let h = 2166136261
  for (const char of text) h = Math.imul(h ^ char.charCodeAt(0), 16777619) >>> 0
  return h
}

/** Today's problem: picked from the root problems by the learner's local date. */
export function dailyProblem(index: BankIndex, date: Date): ProblemSummary | null {
  const roots = index.problems.filter((p) => p.variant_of === null).sort((a, b) => a.id.localeCompare(b.id))
  return roots.length ? roots[hash(localDate(date)) % roots.length] : null
}

const dayBefore = (date: Date) => new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1)

/** Distinct problems solved on each local day. */
function solvedPerDay(attempts: readonly Attempt[]): Map<string, number> {
  const perDay = new Map<string, Set<string>>()
  for (const a of attempts) {
    if (!a.correct) continue
    perDay.set(a.local_date, (perDay.get(a.local_date) ?? new Set()).add(a.problem_id))
  }
  return new Map([...perDay].map(([day, ids]) => [day, ids.size]))
}

/** Days in a row with at least one problem solved, ending today (or yesterday, if not yet today). */
export function dayStreak(attempts: readonly Attempt[], today: Date): number {
  const perDay = solvedPerDay(attempts)
  let day = perDay.has(localDate(today)) ? today : dayBefore(today)
  let streak = 0
  while (perDay.has(localDate(day))) {
    streak++
    day = dayBefore(day)
  }
  return streak
}

/** The last `days` days, oldest first, each with a shade from 0 (none) to 3 (3+ problems solved). */
export function heatmap(attempts: readonly Attempt[], today: Date, days = 35): { date: string; level: number }[] {
  const perDay = solvedPerDay(attempts)
  const cells = []
  let day = today
  for (let i = 0; i < days; i++) {
    const date = localDate(day)
    cells.push({ date, level: Math.min(3, perDay.get(date) ?? 0) })
    day = dayBefore(day)
  }
  return cells.reverse()
}
