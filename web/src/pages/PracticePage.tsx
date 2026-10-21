import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { loadIndex } from '../lib/bank'
import { TryDots } from '../components/TryDots'
import { problemProgress, progressStore, solvedProblemIds } from '../lib/progress'
import type { BankIndex, Kind, MethodInfo, ProblemSummary } from '../types/problem'

const KIND_LABEL: Record<Kind, string> = { counting: 'Counting', probability: 'Probability' }

/**
 * /practice: a temporary list of methods grouped by roadmap node (until the roadmap Home in
 * milestone 9), and /practice?method=…&kind=… for the filtered problem list.
 */
export function PracticePage() {
  const [params] = useSearchParams()
  const [index, setIndex] = useState<BankIndex | null>(null)
  const [error, setError] = useState<string | null>(null)
  const solved = useMemo(() => solvedProblemIds(progressStore.list()), [])

  useEffect(() => {
    loadIndex().then(setIndex, (e: Error) => setError(e.message))
  }, [])

  if (error) return <p className="mx-auto max-w-3xl px-4 py-8 text-ink-muted">{error}</p>
  if (!index) return <p className="mx-auto max-w-3xl px-4 py-8 text-ink-muted">Loading…</p>

  const method = params.get('method')
  const kind = params.get('kind') as Kind | null
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {method || kind ? (
        <ProblemList index={index} method={method} kind={kind} solved={solved} />
      ) : (
        <MethodList index={index} solved={solved} />
      )}
    </div>
  )
}

function progressFor(problems: ProblemSummary[], solved: Set<string>) {
  return { done: problems.filter((p) => solved.has(p.id)).length, total: problems.length }
}

function ProgressBar({ done, total }: { done: number; total: number }) {
  return (
    <div className="h-1.5 w-24 overflow-hidden rounded-full bg-border" aria-hidden="true">
      <div className="h-full bg-accent" style={{ width: total ? `${(100 * done) / total}%` : '0%' }} />
    </div>
  )
}

function MethodList({ index, solved }: { index: BankIndex; solved: Set<string> }) {
  const byMethod = (method: string) => index.problems.filter((p) => p.tags.methods.includes(method))
  return (
    <>
      <h1 className="text-2xl font-bold">Practice by method</h1>
      <p className="mt-1 text-ink-muted">
        Pick a technique to drill. This simple list stands in until the roadmap is built.
      </p>
      {index.roadmap.map((node) => {
        const nodeProblems = index.problems.filter((p) => node.topics.includes(p.tags.topics[0]))
        return (
          <section key={node.id} className="mt-8" aria-labelledby={`node-${node.id}`}>
            <h2 id={`node-${node.id}`} className="font-bold">
              {node.title}
            </h2>
            <p className="text-sm text-ink-muted">{node.blurb}</p>
            <ul className="mt-3 divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
              {node.methods.length > 0 ? (
                node.methods.map((m) => <MethodRow key={m.id} method={m} problems={byMethod(m.id)} solved={solved} />)
              ) : (
                <li className="px-4 py-3 text-sm text-ink-muted">
                  {nodeProblems.length > 0 ? (
                    <Link className="font-bold text-accent-ink hover:underline" to="/practice?kind=probability">
                      Practice probability problems
                    </Link>
                  ) : (
                    'Coming soon'
                  )}
                </li>
              )}
            </ul>
          </section>
        )
      })}
    </>
  )
}

function MethodRow({ method, problems, solved }: { method: MethodInfo; problems: ProblemSummary[]; solved: Set<string> }) {
  const { done, total } = progressFor(problems, solved)
  const label = (
    <>
      <span className="font-bold">{method.name}</span>
      <span className="block text-sm text-ink-muted">{method.blurb}</span>
    </>
  )
  return (
    <li className="flex items-center gap-4 px-4 py-3">
      <div className="min-w-0 flex-1">
        {total > 0 ? (
          <Link to={`/practice?method=${encodeURIComponent(method.id)}`} className="block hover:text-accent-ink">
            {label}
          </Link>
        ) : (
          <div className="opacity-70">{label}</div>
        )}
      </div>
      {total > 0 ? (
        <div className="flex shrink-0 items-center gap-2 text-sm text-ink-muted">
          <ProgressBar done={done} total={total} />
          <span>
            {done} / {total}
          </span>
        </div>
      ) : (
        <span className="shrink-0 text-sm text-ink-muted">Coming soon</span>
      )}
    </li>
  )
}

function ProblemList(props: { index: BankIndex; method: string | null; kind: Kind | null; solved: Set<string> }) {
  const { index, method, kind, solved } = props
  const attempts = useMemo(() => progressStore.list(), [])
  const info = index.roadmap.flatMap((n) => n.methods).find((m) => m.id === method)
  const inMethod = index.problems.filter((p) => !method || p.tags.methods.includes(method))
  const shown = inMethod
    .filter((p) => !kind || p.kind === kind)
    .sort((a, b) => a.family_id.localeCompare(b.family_id) || Number(!!a.variant_of) - Number(!!b.variant_of))
  const link = (k: Kind | null) => {
    const query = new URLSearchParams()
    if (method) query.set('method', method)
    if (k) query.set('kind', k)
    return `/practice?${query.toString()}`
  }
  const { done, total } = progressFor(inMethod, solved)

  return (
    <>
      <Link to="/practice" className="text-sm font-bold text-accent-ink hover:underline">
        ← All methods
      </Link>
      <h1 className="mt-2 text-2xl font-bold">{info?.name ?? (kind ? KIND_LABEL[kind] : 'Practice')}</h1>
      {info && <p className="mt-1 text-ink-muted">{info.blurb}</p>}
      <div className="mt-4 flex flex-wrap items-center gap-4">
        <nav aria-label="Kind" className="flex gap-2 text-sm">
          {([null, 'counting', 'probability'] as const).map((k) => (
            <Link
              key={k ?? 'all'}
              to={link(k)}
              aria-current={kind === k ? 'true' : undefined}
              className={`rounded-full border px-3 py-1 font-bold ${
                kind === k ? 'border-accent-ink bg-accent-soft text-accent-ink' : 'border-border text-ink-muted hover:text-ink'
              }`}
            >
              {k ? KIND_LABEL[k] : 'All'}
            </Link>
          ))}
        </nav>
        {method && (
          <span className="flex items-center gap-2 text-sm text-ink-muted">
            <ProgressBar done={done} total={total} /> {done} / {total} solved
          </span>
        )}
      </div>
      {shown.length === 0 ? (
        <p className="mt-6 text-ink-muted">No problems here yet.</p>
      ) : (
        <ul className="mt-4 divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
          {shown.map((p) => (
            <li key={p.id}>
              <Link to={`/problem/${encodeURIComponent(p.id)}`} className="flex items-center gap-3 px-4 py-3 hover:bg-card-sunken">
                <span className="min-w-0 flex-1">
                  <span className="font-bold">{p.title}</span>
                  {p.twist && <span className="block text-sm text-ink-muted">Variation: {p.twist}</span>}
                </span>
                <span className="flex shrink-0 gap-2 text-xs">
                  <Chip>{KIND_LABEL[p.kind]}</Chip>
                  <Chip>{p.difficulty}</Chip>
                </span>
                <span className="flex w-24 shrink-0 justify-end">
                  <TryDots tries={problemProgress(attempts, p.id).tries} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

function Chip({ children }: { children: React.ReactNode }) {
  return <span className="rounded-md border border-border px-2 py-0.5 text-ink-muted capitalize">{children}</span>
}
