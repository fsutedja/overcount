import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { loadIndex } from '../lib/bank'
import { Difficulty } from '../components/Difficulty'
import { MethodLesson } from '../components/MethodLesson'
import { TryDots } from '../components/TryDots'
import { problemProgress, progressStore, solvedProblemIds } from '../lib/progress'
import type { BankIndex, Kind, MethodInfo, ProblemSummary } from '../types/problem'

const KIND_LABEL: Record<Kind, string> = {
  counting: 'Counting',
  probability: 'Probability',
}
const DIFFICULTIES = ['easy', 'medium', 'hard'] as const
const CONTEXT_LABEL: Record<string, string> = {
  dice: 'Dice',
  'cards-poker': 'Cards',
  'balls-urns': 'Balls and urns',
  'committees-seating': 'Committees and seating',
}

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
  const tab = params.get('tab') === 'learn' ? 'learn' : 'practice'
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {method || kind ? (
        <ProblemList index={index} method={method} kind={kind} tab={tab} solved={solved} />
      ) : (
        <MethodList index={index} solved={solved} />
      )}
    </div>
  )
}

function progressFor(problems: ProblemSummary[], solved: Set<string>) {
  return {
    done: problems.filter((p) => solved.has(p.id)).length,
    total: problems.length,
  }
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
      {/* The header already shows which page this is; the heading is kept for screen readers. */}
      <h1 className="sr-only">Practice by method</h1>
      {index.roadmap.map((node) => {
        const nodeProblems = index.problems.filter((p) => node.topics.includes(p.tags.topics[0]))
        return (
          <section key={node.id} className="mt-8 first-of-type:mt-0" aria-labelledby={`node-${node.id}`}>
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

function MethodRow({
  method,
  problems,
  solved,
}: {
  method: MethodInfo
  problems: ProblemSummary[]
  solved: Set<string>
}) {
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

function ProblemList(props: {
  index: BankIndex
  method: string | null
  kind: Kind | null
  tab: 'practice' | 'learn'
  solved: Set<string>
}) {
  const { index, method, kind, tab, solved } = props
  const attempts = useMemo(() => progressStore.list(), [])
  const [params, setParams] = useSearchParams()
  const difficulty = DIFFICULTIES.find((d) => d === params.get('difficulty')) ?? null
  const context = params.get('context')
  const info = index.roadmap.flatMap((n) => n.methods).find((m) => m.id === method)
  const inMethod = index.problems.filter((p) => !method || p.tags.methods.includes(method))
  const contexts = [...new Set(inMethod.flatMap((p) => p.tags.contexts))].sort()
  const shown = inMethod
    .filter((p) => !kind || p.kind === kind)
    .filter((p) => !difficulty || p.difficulty === difficulty)
    .filter((p) => !context || p.tags.contexts.includes(context))
    .sort((a, b) => a.family_id.localeCompare(b.family_id) || Number(!!a.variant_of) - Number(!!b.variant_of))
  /** The current filters with some changed (null removes one). */
  const withFilters = (changes: Record<string, string | null>) => {
    const query = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value === null) query.delete(key)
      else query.set(key, value)
    }
    return query
  }
  const link = (k: Kind | null, t: 'practice' | 'learn' = 'practice') =>
    `/practice?${withFilters({ kind: k, tab: t === 'learn' ? 'learn' : null }).toString()}`
  const chip = (active: boolean) =>
    `rounded-full border px-3 py-1 font-bold ${
      active ? 'border-accent-ink bg-accent-soft text-accent-ink' : 'border-border text-ink-muted hover:text-ink'
    }`
  const { done, total } = progressFor(inMethod, solved)

  return (
    <>
      <Link to="/practice" className="text-sm font-bold text-accent-ink hover:underline">
        ← All methods
      </Link>
      <h1 className="mt-2 text-2xl font-bold">{info?.name ?? (kind ? KIND_LABEL[kind] : 'Practice')}</h1>
      {info && <p className="mt-1 text-ink-muted">{info.blurb}</p>}
      {method && (
        // Practice | Learn (DESIGN.md, D6): the page always opens on Practice; Learn is opened by hand.
        <nav aria-label="Method page" className="mt-4 flex gap-1 border-b border-border">
          {(['practice', 'learn'] as const).map((t) => (
            <Link
              key={t}
              to={link(kind, t)}
              aria-current={tab === t ? 'page' : undefined}
              className={`-mb-px border-b-[3px] px-3 py-2 font-bold ${
                tab === t ? 'border-accent-ink text-accent-ink' : 'border-transparent text-ink-muted hover:text-ink'
              }`}
            >
              {t === 'practice' ? `Practice (${inMethod.length})` : 'Learn'}
            </Link>
          ))}
        </nav>
      )}
      {method && tab === 'learn' ? (
        <div className="mt-5">
          <MethodLesson method={method} />
        </div>
      ) : (
        practiceTab()
      )}
    </>
  )

  // A plain helper (not a component), so the list isn't remounted on every render.
  function practiceTab() {
    return (
      <>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          {/* One chip row (DESIGN.md, D10): kind | difficulty | context. */}
          <nav aria-label="Filters" className="flex flex-wrap items-center gap-2 text-sm">
            {([null, 'counting', 'probability'] as const).map((k) => (
              <Link key={k ?? 'all'} to={link(k)} aria-current={kind === k ? 'true' : undefined} className={chip(kind === k)}>
                {k ? KIND_LABEL[k] : 'All'}
              </Link>
            ))}
            <span className="mx-1 h-[18px] w-px bg-border" aria-hidden="true" />
            {DIFFICULTIES.map((d) => (
              <Link
                key={d}
                // Clicking the chosen difficulty again clears it.
                to={`/practice?${withFilters({ difficulty: difficulty === d ? null : d }).toString()}`}
                aria-current={difficulty === d ? 'true' : undefined}
                className={`${chip(difficulty === d)} capitalize`}
              >
                {d}
              </Link>
            ))}
            <span className="mx-1 h-[18px] w-px bg-border" aria-hidden="true" />
            <label className="flex items-center">
              <span className="sr-only">Context</span>
              <select
                value={context ?? ''}
                onChange={(event) => setParams(withFilters({ context: event.target.value || null }))}
                className="rounded-lg border border-border bg-card px-2.5 py-1 font-bold text-ink"
              >
                <option value="">Context: All</option>
                {contexts.map((c) => (
                  <option key={c} value={c}>
                    Context: {CONTEXT_LABEL[c] ?? c}
                  </option>
                ))}
              </select>
            </label>
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
                <Link
                  to={`/problem/${encodeURIComponent(p.id)}${method ? `?method=${encodeURIComponent(method)}` : ''}`}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 hover:bg-card-sunken"
                >
                  <span className="min-w-[12rem] flex-1">
                    {/* Try marks follow the title after a thin divider: at most 3 wrong rings plus the green dot. */}
                    <span className="inline-flex flex-wrap items-center gap-x-2.5">
                      <span className="font-bold">{p.title}</span>
                      {problemProgress(attempts, p.id).tries.length > 0 && (
                        <>
                          <span className="h-3.5 w-px bg-border" aria-hidden="true" />
                          <TryDots tries={problemProgress(attempts, p.id).tries} max={3} />
                        </>
                      )}
                    </span>
                    {p.twist && <span className="block text-sm text-ink-muted">Variation: {p.twist}</span>}
                  </span>
                  <span className="flex shrink-0 gap-2 text-xs">
                    <Chip>{KIND_LABEL[p.kind]}</Chip>
                    <Difficulty level={p.difficulty} />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </>
    )
  }
}

function Chip({ children }: { children: React.ReactNode }) {
  return <span className="rounded-md border border-border px-2 py-0.5 text-ink-muted capitalize">{children}</span>
}
