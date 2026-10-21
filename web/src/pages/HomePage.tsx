import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { recordedAttempts } from '../lib/attempts'
import { loadIndex } from '../lib/bank'
import { currentNode, dailyProblem, dayStreak, heatmap, mapRows, methodTally, nodeTally, type Tally } from '../lib/home'
import { solvedProblemIds } from '../lib/progress'
import type { BankIndex, RoadmapNode } from '../types/problem'

/**
 * Home (DESIGN.md, D3): the learning path, today's problem and recent activity. Wide screens get
 * the branching map with the cards in a side column; phones get the same stops as one path.
 */
export function HomePage() {
  const [index, setIndex] = useState<BankIndex | null>(null)
  const [error, setError] = useState<string | null>(null)
  const attempts = useMemo(() => recordedAttempts(), [])
  // "Today" is fixed when the page opens, so the daily problem doesn't change mid-visit.
  const [today] = useState(() => new Date())
  const solved = useMemo(() => solvedProblemIds(attempts), [attempts])
  /** The stop picked on the map (wide screens); its methods show in the side column. */
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    loadIndex().then(setIndex, (e: Error) => setError(e.message))
  }, [])

  if (error) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">{error}</p>
  if (!index) return <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Loading…</p>

  const current = currentNode(index, solved)
  const chosen = index.roadmap.find((n) => n.id === (selected ?? current)) ?? index.roadmap[0]
  const daily = <DailyCard index={index} today={today} />
  const activity = <ActivityCard streak={dayStreak(attempts, today)} solved={solved.size} cells={heatmap(attempts, today)} />

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 md:py-8">
      <h1 className="sr-only">Overcount</h1>
      {/* Phones: cards first, then the path. */}
      <div className="grid gap-4 md:hidden">
        {daily}
        {activity}
        <RoadmapPath index={index} solved={solved} current={current} />
      </div>
      {/* Wide screens: the map, with the cards in a side column. */}
      <div className="hidden gap-6 md:grid md:grid-cols-[minmax(0,1fr)_18rem]">
        <RoadmapMap index={index} solved={solved} current={current} selected={chosen?.id} onSelect={setSelected} />
        <div className="grid content-start gap-4">
          {daily}
          {chosen && <StopDetails index={index} node={chosen} solved={solved} />}
          {activity}
        </div>
      </div>
    </div>
  )
}

interface RoadmapProps {
  index: BankIndex
  solved: ReadonlySet<string>
  current: string | null
}

function ProgressBar({ done, total }: Tally) {
  return (
    <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-border" aria-hidden="true">
      <div className="h-full bg-accent" style={{ width: total ? `${(100 * done) / total}%` : '0%' }} />
    </div>
  )
}

const tallyText = ({ done, total }: Tally) => (total ? `${done} / ${total} solved` : 'coming soon')

/** A stop's methods as chips with solved / total, each linking to its practice list. */
function MethodChips({ index, node, solved }: { index: BankIndex; node: RoadmapNode; solved: ReadonlySet<string> }) {
  if (!node.methods.length) return <p className="text-sm text-ink-muted">Problems for this stop are coming soon.</p>
  return (
    <div className="flex flex-wrap gap-1.5">
      {node.methods.map((method) => {
        const { done, total } = methodTally(index, method.id, solved)
        return (
          <Link
            key={method.id}
            to={`/practice?method=${encodeURIComponent(method.id)}`}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-0.5 text-sm font-bold text-accent-ink hover:bg-card-sunken"
          >
            {method.name}
            <span className="font-normal text-ink-muted">
              {done}/{total}
            </span>
          </Link>
        )
      })}
    </div>
  )
}

const ROW_HEIGHT = 112
const CARD_HEIGHT = 76

/** The picked stop's blurb and methods, in the side column next to the map. */
function StopDetails({ index, node, solved }: { index: BankIndex; node: RoadmapNode; solved: ReadonlySet<string> }) {
  return (
    <section className="rounded-xl border border-border bg-card px-4 py-3" aria-live="polite" aria-labelledby="stop-title">
      <h2 id="stop-title" className="font-bold">
        {node.title}
      </h2>
      <p className="mb-2 text-sm text-ink-muted">{node.blurb}</p>
      <MethodChips index={index} node={node} solved={solved} />
    </section>
  )
}

/** D3 · B: stops on a small map, joined to the stops they follow. Clicking one shows its methods. */
function RoadmapMap({
  index,
  solved,
  current,
  selected,
  onSelect,
}: RoadmapProps & { selected?: string; onSelect: (id: string) => void }) {
  const rows = mapRows(index.roadmap)
  const byRow = new Map<number, RoadmapNode[]>()
  for (const node of index.roadmap) byRow.set(rows.get(node.id)!, [...(byRow.get(rows.get(node.id)!) ?? []), node])
  const position = new Map<string, { x: number; y: number }>()
  for (const [row, nodes] of byRow) {
    nodes.forEach((node, i) => position.set(node.id, { x: ((i + 1) / (nodes.length + 1)) * 100, y: row * ROW_HEIGHT }))
  }
  const height = (Math.max(...rows.values()) + 1) * ROW_HEIGHT

  return (
    <section aria-label="Learning path">
      <div className="relative" style={{ height }}>
        <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="none" aria-hidden="true">
          {index.roadmap.flatMap((node) =>
            node.after.map((from) => {
              const a = position.get(from)!
              const b = position.get(node.id)!
              return (
                <line
                  key={`${from}-${node.id}`}
                  x1={`${a.x}%`}
                  y1={a.y + CARD_HEIGHT}
                  x2={`${b.x}%`}
                  y2={b.y}
                  strokeWidth={3}
                  className="stroke-border"
                />
              )
            }),
          )}
        </svg>
        {index.roadmap.map((node) => {
          const { x, y } = position.get(node.id)!
          const counts = nodeTally(index, node, solved)
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => onSelect(node.id)}
              aria-pressed={selected === node.id}
              className={`absolute w-48 -translate-x-1/2 rounded-xl border bg-card px-3 py-2 text-left hover:bg-card-sunken ${
                node.id === current ? 'border-2 border-accent-ink' : 'border-border'
              } ${counts.total ? '' : 'opacity-55'} ${selected === node.id ? 'ring-2 ring-accent ring-offset-2 ring-offset-bg' : ''}`}
              style={{ left: `${x}%`, top: y, height: CARD_HEIGHT }}
            >
              <span className="block text-[15px] font-bold leading-tight">{node.title}</span>
              <span className="block text-xs text-ink-muted">{tallyText(counts)}</span>
              {counts.total > 0 && <ProgressBar {...counts} />}
            </button>
          )
        })}
      </div>
    </section>
  )
}

/** D3 · A on phones: the same stops on one dotted path. The current stop is open. */
function RoadmapPath({ index, solved, current }: RoadmapProps) {
  const [open, setOpen] = useState<string | null>(current ?? index.roadmap[0]?.id ?? null)
  return (
    <section aria-label="Learning path">
      <ol className="relative grid gap-3.5 before:absolute before:top-5 before:bottom-5 before:left-[22px] before:border-l-[3px] before:border-dotted before:border-border">
        {index.roadmap.map((node, i) => {
          const counts = nodeTally(index, node, solved)
          const finished = counts.total > 0 && counts.done === counts.total
          const isOpen = open === node.id
          return (
            <li key={node.id} className={`relative grid grid-cols-[46px_1fr] items-start gap-2.5 ${counts.total ? '' : 'opacity-55'}`}>
              <span
                className={`z-10 grid size-[46px] place-items-center rounded-full border-[3px] font-bold ${
                  finished
                    ? 'border-accent bg-accent text-on-accent'
                    : node.id === current
                      ? 'border-accent-ink bg-card text-accent-ink'
                      : 'border-border bg-card'
                }`}
              >
                {i + 1}
              </span>
              <div className="rounded-xl border border-border bg-card px-3.5 py-2.5">
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : node.id)}
                  aria-expanded={isOpen}
                  className="flex w-full items-baseline justify-between gap-3 text-left"
                >
                  <span className="font-bold">{node.title}</span>
                  <span className="shrink-0 text-xs text-ink-muted">{tallyText(counts)}</span>
                </button>
                {counts.total > 0 && <ProgressBar {...counts} />}
                {isOpen && (
                  <div className="mt-2">
                    <p className="mb-2 text-sm text-ink-muted">{node.blurb}</p>
                    <MethodChips index={index} node={node} solved={solved} />
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}

function DailyCard({ index, today }: { index: BankIndex; today: Date }) {
  const problem = dailyProblem(index, today)
  if (!problem) return null
  const date = today.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
  return (
    <section className="rounded-xl border border-border bg-card px-4 py-3" aria-labelledby="daily-title">
      <p className="text-sm text-ink-muted">
        <span className="font-pixel">daily problem</span> · {date}
      </p>
      <h2 id="daily-title" className="mt-1 text-lg font-bold">
        {problem.title}
      </h2>
      {/* No method name here: naming it would give the problem away (D6 spoiler rule). */}
      <p className="mb-3 text-sm text-ink-muted capitalize">
        {problem.difficulty} · {problem.kind}
      </p>
      <Link
        to={`/problem/${encodeURIComponent(problem.id)}`}
        className="inline-block rounded-lg bg-accent-ink px-3.5 py-1.5 text-sm font-bold text-on-accent hover:opacity-90"
      >
        Solve it
      </Link>
    </section>
  )
}

const HEAT = ['bg-card-sunken border-border', 'bg-accent-soft border-border', 'bg-accent border-accent', 'bg-accent-ink border-accent-ink']

function ActivityCard({ streak, solved, cells }: { streak: number; solved: number; cells: { date: string; level: number }[] }) {
  return (
    <section className="rounded-xl border border-border bg-card px-4 py-3" aria-label="Your activity">
      <p className="mb-2 flex justify-between">
        <span>
          <b>{streak}</b> <span className="font-pixel text-sm text-ink-muted">day streak</span>
        </span>
        <span>
          <b>{solved}</b> <span className="font-pixel text-sm text-ink-muted">solved</span>
        </span>
      </p>
      <div className="grid grid-cols-[repeat(15,minmax(0,1fr))] gap-[3px]" role="img" aria-label={`Problems solved per day over the last ${cells.length} days`}>
        {cells.map((cell) => (
          <span key={cell.date} title={cell.date} className={`aspect-square rounded-[3px] border ${HEAT[cell.level]}`} />
        ))}
      </div>
      <p className="mt-2 text-xs text-ink-muted">Last 5 weeks · darker = more solved</p>
    </section>
  )
}
