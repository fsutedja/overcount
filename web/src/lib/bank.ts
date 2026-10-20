import type { BankIndex, Family, Problem } from '../types/problem'

/** Loads the static problem bank built by the pipeline (web/public/bank/). */

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) throw new Error(`Couldn't load ${path} (${response.status})`)
  return (await response.json()) as T
}

export const loadIndex = () => getJson<BankIndex>('/bank/index.json')

export const loadFamily = (familyId: string) => getJson<Family>(`/bank/families/${encodeURIComponent(familyId)}.json`)

export async function loadProblem(problemId: string): Promise<Problem> {
  const index = await loadIndex()
  const summary = index.problems.find((p) => p.id === problemId)
  if (!summary) throw new Error(`There's no problem called "${problemId}".`)
  const family = await loadFamily(summary.family_id)
  const problem = family.problems.find((p) => p.id === problemId)
  if (!problem) throw new Error(`Problem "${problemId}" is missing from its family file.`)
  return problem
}
