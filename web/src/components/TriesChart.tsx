import { useState } from 'react'

interface Day {
  date: string
  tries: number
  right: number
}

const W = 600
const H = 200
const LEFT = 28
const RIGHT = 44
const TOP = 12
const BOTTOM = 24

const shortDate = (date: string) => new Date(`${date}T12:00:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })

/**
 * Tries per day (DESIGN.md, D8): two lines on one axis, "tries" dashed in muted ink and "right"
 * solid in accent, each labelled at its end, with a hover crosshair and tooltip.
 */
export function TriesChart({ days }: { days: Day[] }) {
  const [hover, setHover] = useState<number | null>(null)
  const max = Math.max(4, ...days.map((d) => d.tries))
  const top = Math.ceil(max / 2) * 2
  const x = (i: number) => LEFT + (i * (W - LEFT - RIGHT)) / Math.max(1, days.length - 1)
  const y = (v: number) => TOP + (H - TOP - BOTTOM) * (1 - v / top)
  const path = (key: 'tries' | 'right') => days.map((d, i) => `${i ? 'L' : 'M'}${x(i)},${y(d[key])}`).join(' ')
  const ticks = [0, top / 2, top]
  const last = days.length - 1
  const close = Math.abs(y(days[last].tries) - y(days[last].right)) < 12
  const totalTries = days.reduce((s, d) => s + d.tries, 0)
  const totalRight = days.reduce((s, d) => s + d.right, 0)

  const onMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect()
    const px = ((event.clientX - box.left) / box.width) * W
    const i = Math.round(((px - LEFT) / (W - LEFT - RIGHT)) * last)
    setHover(Math.max(0, Math.min(last, i)))
  }

  return (
    <section className="min-w-0 rounded-xl border border-border bg-card px-4 py-3" aria-labelledby="tries-title">
      <h3 id="tries-title" className="font-bold">
        Tries per day <span className="text-sm font-normal text-ink-muted">· last {days.length} days</span>
      </h3>
      <p className="sr-only">
        {totalTries} tries, {totalRight} right, over the last {days.length} days.
      </p>
      <div className="relative mt-2">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="block h-auto w-full"
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
          aria-hidden="true"
        >
          {ticks.map((t) => (
            <g key={t}>
              <line x1={LEFT} x2={W - RIGHT} y1={y(t)} y2={y(t)} strokeWidth={1} className="stroke-border" />
              <text x={LEFT - 6} y={y(t) + 4} textAnchor="end" fontSize={11} className="fill-ink-muted">
                {t}
              </text>
            </g>
          ))}
          <text x={LEFT} y={H - 6} fontSize={11} className="fill-ink-muted">
            {shortDate(days[0].date)}
          </text>
          <text x={W - RIGHT} y={H - 4} textAnchor="end" fontSize={11} className="fill-ink-muted">
            today
          </text>
          <path d={path('tries')} fill="none" strokeWidth={2} strokeDasharray="5 4" strokeLinejoin="round" className="stroke-ink-muted" />
          <path d={path('right')} fill="none" strokeWidth={2} strokeLinejoin="round" className="stroke-accent" />
          {/* End labels; when the lines end close together, nudge them apart. */}
          <text x={W - RIGHT + 6} y={y(days[last].tries) + (close ? -3 : 4)} fontSize={11} className="fill-ink-muted">
            tries
          </text>
          <text x={W - RIGHT + 6} y={y(days[last].right) + (close ? 11 : 4)} fontSize={11} className="fill-ink">
            right
          </text>
          {hover !== null && (
            <g>
              <line x1={x(hover)} x2={x(hover)} y1={TOP} y2={H - BOTTOM} strokeWidth={1} className="stroke-ink-muted" />
              <circle cx={x(hover)} cy={y(days[hover].tries)} r={4} strokeWidth={2} className="fill-card stroke-ink-muted" />
              <circle cx={x(hover)} cy={y(days[hover].right)} r={4} strokeWidth={2} className="fill-card stroke-accent" />
            </g>
          )}
          {/* A wide transparent strip so hovering anywhere over the plot works. */}
          <rect x={LEFT} y={TOP} width={W - LEFT - RIGHT} height={H - TOP - BOTTOM} fill="transparent" />
        </svg>
        {hover !== null && (
          <div
            className="pointer-events-none absolute top-0 z-10 -translate-x-1/2 rounded-md border border-border bg-card px-2 py-1 text-xs whitespace-nowrap shadow-sm"
            style={{ left: `${(x(hover) / W) * 100}%` }}
          >
            {shortDate(days[hover].date)} · <b>{days[hover].tries}</b> tries · <b>{days[hover].right}</b> right
          </div>
        )}
      </div>
      <div className="mt-1 flex gap-4 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <svg width="18" height="6" aria-hidden="true">
            <line x1="0" x2="18" y1="3" y2="3" strokeWidth={2} strokeDasharray="5 4" className="stroke-ink-muted" />
          </svg>
          tries
        </span>
        <span className="flex items-center gap-1.5">
          <svg width="18" height="6" aria-hidden="true">
            <line x1="0" x2="18" y1="3" y2="3" strokeWidth={2} className="stroke-accent" />
          </svg>
          right
        </span>
      </div>
    </section>
  )
}
