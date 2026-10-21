import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ActivityCalendar } from '../components/ActivityCalendar'
import { TriesChart } from '../components/TriesChart'
import { TryDots } from '../components/TryDots'
import { recordedAttempts } from '../lib/attempts'
import { loadIndex } from '../lib/bank'
import { dayStreak, nodeProblems } from '../lib/home'
import type { ProblemStatus } from '../lib/progress'
import { bestStreak, calendar, problemRows, triesPerDay, type ProblemRow } from '../lib/stats'
import type { BankIndex } from '../types/problem'

// "Mastered" isn't shown on this page (it still exists in the data); it counts as solved.
const FILTERS: { id: 'all' | ProblemStatus; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'solved', label: 'Solved' },
  { id: 'tried', label: 'Tried' },
  { id: 'new', label: 'Not started' },
]
const shownStatus = (status: ProblemStatus): ProblemStatus => (status === 'mastered' ? 'solved' : status)
const STATUS_LABEL: Record<ProblemStatus, string> = { mastered: 'solved', solved: 'solved', tried: 'tried', new: 'not started' }

/** /progress (DESIGN.md, D8): Overview and Problems tabs, all derived from the attempt log. */
export function ProgressPage() {
  const [params] = useSearchParams()
  const tab = params.get('tab') === 'problems' ? 'problems' : 'overview'
  const [index, setIndex] = useState<BankIndex | null>(null)
  const [error, setError] = useState<string | null>(null)
  const attempts = useMemo(() => recordedAttempts(), [])
  const [today] = useState(() => new Date())

  useEffect(() => {
    loadIndex().then(setIndex, (e: Error) => setError(e.message))
  }, [])

  if (error) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">{error}</p>
  if (!index) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Loading…</p>

  const rows = problemRows(
    attempts,
    index.problems.map((p) => p.id),
  )
  const byId = new Map(rows.map((r) => [r.id, r]))
  const count = (status: ProblemStatus) => rows.filter((r) => r.status === status).length

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 md:py-8">
      {/* The header already shows which page this is; the heading is kept for screen readers. */}
      <h1 className="sr-only">Progress</h1>
      <nav aria-label="Progress views" className="flex gap-1 border-b border-border">
        {(['overview', 'problems'] as const).map((t) => (
          <Link
            key={t}
            to={t === 'overview' ? '/progress' : '/progress?tab=problems'}
            aria-current={tab === t ? 'page' : undefined}
            className={`-mb-px border-b-[3px] px-3 py-2 font-bold ${
              tab === t ? 'border-accent-ink text-accent-ink' : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            {t === 'overview' ? 'Overview' : `Problems (${rows.length})`}
          </Link>
        ))}
      </nav>
      {tab === 'overview' ? (
        <div className="mt-5 grid gap-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Tile value={count('mastered') + count('solved')} label="solved" />
            <Tile value={attempts.length} label="tries" />
            <Tile value={dayStreak(attempts, today)} label="day streak" />
            <Tile value={bestStreak(attempts)} label="best streak" />
          </div>
          <div className="grid gap-4 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
            <div className="grid min-w-0 content-start gap-4">
              <ActivityCalendar {...calendar(attempts, today)} />
              <TriesChart days={triesPerDay(attempts, today)} />
            </div>
            <ByStop index={index} byId={byId} />
          </div>
        </div>
      ) : (
        <ProblemsTab index={index} rows={rows} filter={params.get('status')} />
      )}
    </div>
  )
}

function Tile({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3">
      <b className="block text-2xl leading-tight">{value}</b>
      <span className="font-pixel text-sm text-ink-muted">{label}</span>
    </div>
  )
}

function ByStop({ index, byId }: { index: BankIndex; byId: Map<string, ProblemRow> }) {
  return (
    <section className="min-w-0 content-start self-start rounded-xl border border-border bg-card px-4 py-3" aria-labelledby="stops-title">
      <h2 id="stops-title" className="mb-1 font-bold">
        By roadmap stop
      </h2>
      <ul>
        {index.roadmap.map((node) => {
          const statuses = nodeProblems(index, node).map((p) => byId.get(p.id)?.status ?? 'new')
          const total = statuses.length
          const done = statuses.filter((s) => s === 'mastered' || s === 'solved').length
          return (
            <li key={node.id} className={`border-t border-border py-2 first:border-t-0 ${total ? '' : 'opacity-55'}`}>
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[15px] font-bold">{node.title}</span>
                <span className="shrink-0 text-xs text-ink-muted">
                  {total ? `${done} / ${total} solved` : 'coming soon'}
                </span>
              </div>
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-border" aria-hidden="true">
                <div className="h-full bg-accent" style={{ width: total ? `${(100 * done) / total}%` : '0%' }} />
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function ProblemsTab({ index, rows, filter }: { index: BankIndex; rows: ProblemRow[]; filter: string | null }) {
  const active = FILTERS.some((f) => f.id === filter) ? (filter as (typeof FILTERS)[number]['id']) : 'all'
  const titles = new Map(index.problems.map((p) => [p.id, p]))
  const shown = rows.filter((r) => active === 'all' || shownStatus(r.status) === active)
  return (
    <div className="mt-5">
      <nav aria-label="Filter by status" className="flex flex-wrap gap-2 text-sm">
        {FILTERS.map((f) => (
          <Link
            key={f.id}
            to={f.id === 'all' ? '/progress?tab=problems' : `/progress?tab=problems&status=${f.id}`}
            aria-current={active === f.id ? 'true' : undefined}
            className={`rounded-full border px-3 py-1 font-bold ${
              active === f.id ? 'border-accent-ink bg-accent-soft text-accent-ink' : 'border-border text-ink-muted hover:text-ink'
            }`}
          >
            {f.label} ({f.id === 'all' ? rows.length : rows.filter((r) => shownStatus(r.status) === f.id).length})
          </Link>
        ))}
      </nav>
      {shown.length === 0 ? (
        <p className="mt-6 text-ink-muted">Nothing here yet.</p>
      ) : (
        <ul className="mt-4 divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
          {shown.map((row) => {
            const problem = titles.get(row.id)
            return (
              <li key={row.id}>
                <Link
                  to={`/problem/${encodeURIComponent(row.id)}`}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 hover:bg-card-sunken"
                >
                  <span className="min-w-[12rem] flex-1">
                    <span className="font-bold">{problem?.title ?? row.id}</span>
                    {problem?.twist && <span className="block text-sm text-ink-muted">Variation: {problem.twist}</span>}
                  </span>
                  <span className="text-sm text-ink-muted">{STATUS_LABEL[row.status]}</span>
                  <span className="flex min-w-[4.5rem] justify-end">
                    <TryDots tries={row.tries} />
                  </span>
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
