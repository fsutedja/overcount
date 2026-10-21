import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { recordedAttempts } from '../lib/attempts'
import { loadIndex } from '../lib/bank'
import { problemProgress } from '../lib/progress'
import type { BankIndex, Problem } from '../types/problem'
import { TryDots } from './TryDots'

/**
 * The problem list beside a problem (DESIGN.md, D12): the method's problems in Practice-list
 * order, the current one highlighted, each with its try marks. Opened from a method's Practice
 * tab it's titled with that method; from elsewhere it says "Related problems", so the method
 * isn't given away (D6 spoiler rule). Below `lg` it folds into a "Problems" button.
 */
export function ProblemSidebar({ problem, fromMethod }: { problem: Problem; fromMethod: string | null }) {
  const [index, setIndex] = useState<BankIndex | null>(null)
  const [open, setOpen] = useState(false)
  const attempts = useMemo(() => recordedAttempts(), [])
  const method = fromMethod && problem.tags.methods.includes(fromMethod) ? fromMethod : problem.tags.methods[0]

  useEffect(() => {
    loadIndex().then(setIndex, () => setIndex(null))
  }, [])

  if (!index || !method) return null
  const name = index.roadmap.flatMap((n) => n.methods).find((m) => m.id === method)?.name
  const title = fromMethod ? (name ?? 'Problems') : 'Related problems'
  const problems = index.problems
    .filter((p) => p.tags.methods.includes(method))
    .sort((a, b) => a.family_id.localeCompare(b.family_id) || Number(!!a.variant_of) - Number(!!b.variant_of))
  const query = fromMethod ? `?method=${encodeURIComponent(fromMethod)}` : ''

  const list = (
    <nav aria-label={title}>
      <Link
        to={fromMethod ? `/practice?method=${encodeURIComponent(fromMethod)}` : '/practice'}
        className="mb-3 block border-b border-border px-2.5 pt-1 pb-2.5 text-sm font-bold text-accent-ink hover:underline"
      >
        {fromMethod ? '← Back to the list' : '← All methods'}
      </Link>
      <h2 className="mb-2 border-b border-border px-2.5 pb-2.5 text-sm font-bold tracking-wide text-ink-muted uppercase">
        {title}
      </h2>
      <ul className="space-y-1">
        {problems.map((p) => {
          const current = p.id === problem.id
          return (
            <li key={p.id}>
              <Link
                to={`/problem/${encodeURIComponent(p.id)}${query}`}
                aria-current={current ? 'page' : undefined}
                onClick={() => setOpen(false)}
                className={`flex items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-sm ${
                  current
                    ? 'bg-accent-soft font-bold text-accent-ink shadow-[inset_3px_0_0_var(--accent-ink)]'
                    : 'hover:bg-card-sunken'
                }`}
              >
                <span className="min-w-0">{p.title}</span>
                {/* At most 3 wrong-try rings here (older ones become "+n"), so titles keep their width. */}
                <TryDots tries={problemProgress(attempts, p.id).tries} max={3} />
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )

  return (
    <>
      {/* Wide screens: a column beside the problem. */}
      <aside className="hidden lg:mt-[4.25rem] lg:block">
        <div className="sticky top-6 rounded-xl border border-border bg-card p-3">{list}</div>
      </aside>
      {/* Narrower screens: a button that unfolds the same list. */}
      <div className="px-4 pt-4 lg:hidden">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm font-bold text-accent-ink"
        >
          {open ? '▾' : '▸'} Problems
        </button>
        {open && <div className="mt-2 rounded-xl border border-border bg-card p-2">{list}</div>}
      </div>
    </>
  )
}
