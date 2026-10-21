import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { ProblemPage } from '../components/ProblemPage'
import { loadProblem } from '../lib/bank'
import type { Problem } from '../types/problem'

/** Until the roadmap Home exists (milestone 9), "/" shows this problem; ?p=<id> still works. */
const DEFAULT_PROBLEM = 'committee-mixed'

/** /problem/:id, and "/" with an optional ?p=<id>. */
export function ProblemRoute() {
  const { id } = useParams()
  const [params] = useSearchParams()
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
  return (
    <ProblemPage
      key={loaded.problem.id}
      problem={loaded.problem}
      instance={loaded.problem.instances[0]}
      fromMethod={params.get('method')}
    />
  )
}
