import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { ProblemPage } from '../components/ProblemPage'
import { ProblemSidebar } from '../components/ProblemSidebar'
import { loadProblem } from '../lib/bank'
import type { Problem } from '../types/problem'

/** Old "/?p=" links without an id open this problem. */
const DEFAULT_PROBLEM = 'committee-mixed'

/** Fewer number sets than this and "New numbers" is hidden (PLAN.md, milestone 7). */
const MIN_NUMBER_SETS = 5

/** /problem/:id, and "/" with an optional ?p=<id>. */
export function ProblemRoute() {
  const { id } = useParams()
  const [params, setParams] = useSearchParams()
  const problemId = id ?? params.get('p') ?? DEFAULT_PROBLEM
  const [loaded, setLoaded] = useState<{ id: string; problem?: Problem; error?: string } | null>(null)

  useEffect(() => {
    let current = true
    loadProblem(problemId).then(
      (problem) => current && setLoaded({ id: problemId, problem }),
      (e: Error) => current && setLoaded({ id: problemId, error: e.message }),
    )
    return () => {
      current = false
    }
  }, [problemId])

  if (loaded?.id !== problemId) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Loading…</p>
  if (loaded.error || !loaded.problem) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">{loaded.error}</p>
  const { problem } = loaded
  // Which number set is showing lives in the address (?n=<key>), so a reload keeps it.
  const instance = problem.instances.find((i) => i.key === params.get('n')) ?? problem.instances[0]
  const newNumbers = () => {
    const others = problem.instances.filter((i) => i.key !== instance.key)
    const next = others[Math.floor(Math.random() * others.length)]
    const query = new URLSearchParams(params)
    query.set('n', next.key)
    setParams(query, { replace: true })
  }
  return (
    // D12: the problem list sits beside the problem on wide screens (a "Problems" button below).
    <div className="mx-auto max-w-7xl lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:items-start lg:gap-2 lg:px-4">
      <ProblemSidebar key={problem.id} problem={problem} fromMethod={params.get('method')} />
      <ProblemPage
        // A new number set starts a fresh attempt: blanks, Help and solution reset.
        key={`${problem.id}|${instance.key}`}
        problem={problem}
        instance={instance}
        fromMethod={params.get('method')}
        onNewNumbers={problem.instances.length >= MIN_NUMBER_SETS ? newNumbers : undefined}
      />
    </div>
  )
}
