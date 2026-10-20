import { useEffect, useState } from 'react'
import { Header } from './components/Header'
import { ProblemPage } from './components/ProblemPage'
import { loadProblem } from './lib/bank'
import type { Problem } from './types/problem'

/** Until the practice pages exist (milestone 7), pick a problem with ?p=<id>. */
const DEFAULT_PROBLEM = 'committee-mixed'

export default function App() {
  const problemId = new URLSearchParams(window.location.search).get('p') ?? DEFAULT_PROBLEM
  const [problem, setProblem] = useState<Problem | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadProblem(problemId).then(setProblem, (e: Error) => setError(e.message))
  }, [problemId])

  return (
    <>
      <Header />
      <main>
        {error && <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">{error}</p>}
        {!error && !problem && <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Loading…</p>}
        {problem && <ProblemPage key={problem.id} problem={problem} instance={problem.instances[0]} />}
      </main>
    </>
  )
}
