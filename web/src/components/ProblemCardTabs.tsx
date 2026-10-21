import { useEffect, useId, useState } from 'react'
import { loadIndex } from '../lib/bank'
import { loadShowExample, saveShowExample } from '../lib/exampleToggle'
import type { Instance, Problem } from '../types/problem'
import { ExampleBlock } from './ExampleBlock'
import { MethodLesson } from './MethodLesson'

/**
 * The tabs under the problem statement (DESIGN.md, D7): "Example" (always first and the default
 * on every problem) and one "Method: …" tab per method, which shows that method's lesson in the
 * same space, so the answer box is never covered. The ▾ button folds the whole area; that
 * choice is remembered across problems.
 */
export function ProblemCardTabs({ problem, instance, methods }: { problem: Problem; instance: Instance; methods: string[] }) {
  const [open, setOpen] = useState(loadShowExample)
  const [tab, setTab] = useState<string>('example')
  const names = useMethodNames()
  const panelId = useId()
  const shown = methods.filter((m) => names[m]).slice(0, 2)
  const active = tab === 'example' || shown.includes(tab) ? tab : 'example'

  const setOpenAndSave = (next: boolean) => {
    setOpen(next)
    saveShowExample(next)
  }
  const choose = (next: string) => {
    setTab(next)
    if (!open) setOpenAndSave(true)
  }
  const tabButton = (id: string, label: string, title?: string) => (
    <button
      key={id}
      type="button"
      role="tab"
      title={title}
      aria-label={title ?? label}
      aria-selected={open && active === id}
      aria-controls={panelId}
      onClick={() => choose(id)}
      className={`-mb-px shrink-0 border-b-[3px] px-1.5 py-2 text-sm font-bold whitespace-nowrap ${
        open && active === id ? 'border-accent-ink text-accent-ink' : 'border-transparent text-ink-muted hover:text-ink'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="mt-4">
      {/* One line: ▾ Example | method names (DESIGN.md, D7). Scrolls sideways rather than wrapping. */}
      <div className="flex items-end gap-1 overflow-x-auto border-b border-border">
        <button
          type="button"
          onClick={() => setOpenAndSave(!open)}
          aria-expanded={open}
          aria-controls={panelId}
          aria-label={open ? 'Hide examples and methods' : 'Show examples and methods'}
          className="shrink-0 py-2 pr-1 font-bold text-accent-ink"
        >
          <span aria-hidden="true">{open ? '▾' : '▸'}</span>
        </button>
        <div role="tablist" aria-label="About this problem" className="flex items-end">
          {tabButton('example', 'Example')}
          {shown.length > 0 && <span className="mx-1.5 mb-2.5 h-4 w-px shrink-0 self-end bg-border" aria-hidden="true" />}
          {shown.map((m) => tabButton(m, names[m], `Method: ${names[m]}`))}
        </div>
      </div>
      {open && (
        <div id={panelId} role="tabpanel" className="mt-3">
          {active === 'example' ? (
            <ExampleBlock problem={problem} instance={instance} />
          ) : (
            <MethodLesson method={active} compact />
          )}
        </div>
      )}
    </div>
  )
}

/** Method id → display name, from the bank index (already loaded by most pages). */
function useMethodNames(): Record<string, string> {
  const [names, setNames] = useState<Record<string, string>>({})
  useEffect(() => {
    loadIndex().then(
      (index) => setNames(Object.fromEntries(index.roadmap.flatMap((n) => n.methods).map((m) => [m.id, m.name]))),
      () => setNames({}),
    )
  }, [])
  return names
}
