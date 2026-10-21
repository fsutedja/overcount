import { useEffect, useRef, useState } from 'react'
import type { HeatCell } from '../lib/stats'

const SHADE = ['bg-card-sunken border-border', 'bg-accent-soft border-border', 'bg-accent border-accent', 'bg-accent-ink border-accent-ink']
const CELL = 12
const GAP = 3
const DAY_LABELS = ['', 'Mon', '', 'Wed', '', 'Fri', '']

const longDate = (date: string) =>
  new Date(`${date}T12:00:00`).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })

/**
 * GitHub-style activity calendar (DESIGN.md, D8): one column per week (Sunday on top), month
 * names above, Mon / Wed / Fri on the left, shaded by problems solved that day.
 */
export function ActivityCalendar({ columns, months, total }: { columns: HeatCell[][]; months: { column: number; label: string }[]; total: number }) {
  const scroller = useRef<HTMLDivElement>(null)
  const [hover, setHover] = useState<{ cell: HeatCell; left: number; top: number } | null>(null)

  // Start scrolled to the most recent weeks on narrow screens.
  useEffect(() => {
    if (scroller.current) scroller.current.scrollLeft = scroller.current.scrollWidth
  }, [])

  const step = CELL + GAP
  return (
    <section className="min-w-0 rounded-xl border border-border bg-card px-4 py-3" aria-labelledby="calendar-title">
      <h3 id="calendar-title" className="mb-2 font-bold">
        {total} {total === 1 ? 'problem' : 'problems'} solved in the last year
      </h3>
      <div ref={scroller} className="relative overflow-x-auto pb-1">
        <div className="relative" style={{ width: 32 + columns.length * step, height: 18 + 7 * step }}>
          {months.map((m) => (
            <span key={m.column} className="absolute top-0 text-xs text-ink-muted" style={{ left: 32 + m.column * step }}>
              {m.label}
            </span>
          ))}
          {DAY_LABELS.map((label, d) =>
            label ? (
              <span key={d} className="absolute left-0 text-xs leading-none text-ink-muted" style={{ top: 18 + d * step + 1 }}>
                {label}
              </span>
            ) : null,
          )}
          <div role="img" aria-label={`${total} problems solved in the last year, one square per day`}>
            {columns.map((column, w) =>
              column.map((cell, d) =>
                cell.inRange ? (
                  <span
                    key={cell.date}
                    onMouseEnter={() => setHover({ cell, left: 32 + w * step, top: 18 + d * step })}
                    onMouseLeave={() => setHover(null)}
                    className={`absolute rounded-[3px] border ${SHADE[cell.level]}`}
                    style={{ left: 32 + w * step, top: 18 + d * step, width: CELL, height: CELL }}
                  />
                ) : null,
              ),
            )}
          </div>
          {hover && (
            <span
              className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-md border border-border bg-card px-2 py-1 text-xs whitespace-nowrap shadow-sm"
              style={{ left: hover.left + CELL / 2, top: hover.top - 4 }}
            >
              <b>{hover.cell.count}</b> solved · {longDate(hover.cell.date)}
            </span>
          )}
        </div>
      </div>
      <div className="mt-1 flex items-center justify-end gap-1 text-xs text-ink-muted">
        Less
        {SHADE.map((shade) => (
          <span key={shade} className={`size-3 rounded-[3px] border ${shade}`} />
        ))}
        More
      </div>
    </section>
  )
}
