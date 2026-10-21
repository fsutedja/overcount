import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ProblemPage } from '../components/ProblemPage'
import type { Family } from '../types/problem'

/**
 * Dev-only (/dev/preview/:familyId): a staged family on the real problem page, before it's
 * approved. `overcount review` writes web/public/preview/<slug>.json for each passing draft.
 */
export function PreviewRoute() {
  const { familyId = '' } = useParams()
  const [family, setFamily] = useState<Family | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [index, setIndex] = useState(0)

  useEffect(() => {
    fetch(`/preview/${encodeURIComponent(familyId)}.json`)
      .then((r) => (r.ok ? (r.json() as Promise<Family>) : Promise.reject(new Error(`No preview for ${familyId}`))))
      .then(setFamily, (e: Error) => setError(e.message))
  }, [familyId])

  if (error) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">{error}. Run `uv run overcount review`.</p>
  if (!family) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Loading…</p>
  const problem = family.problems[index]
  return (
    <>
      <nav className="mx-auto flex max-w-5xl flex-wrap gap-2 px-4 pt-6 text-sm" aria-label="Problems in this draft">
        <span className="font-bold text-ink-muted">Draft preview:</span>
        {family.problems.map((p, i) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setIndex(i)}
            aria-current={i === index}
            className={`rounded-lg border px-2 py-0.5 ${i === index ? 'border-accent font-bold text-accent-ink' : 'border-border'}`}
          >
            {p.difficulty}: {p.title}
          </button>
        ))}
      </nav>
      <ProblemPage key={problem.id} problem={problem} instance={problem.instances[0]} />
    </>
  )
}
