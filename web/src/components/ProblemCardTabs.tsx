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
  const tabs = [{ id: 'example', label: 'Example' }, ...shown.map((m) => ({ id: m, label: `Method: ${names[m]}` }))]

  return (
    <div className="mt-4">
      <div className="flex items-end gap-1 border-b border-border">
        <button
          type="button"
          onClick={() => setOpenAndSave(!open)}
          aria-expanded={open}
          aria-controls={panelId}
          aria-label={open ? 'Hide examples and methods' : 'Show examples and methods'}
          className="px-1 py-2 font-bold text-accent-ink"
        >
          <span aria-hidden="true">{open ? '▾' : '▸'}</span>
        </button>
        <div role="tablist" aria-label="About this problem" className="flex flex-wrap gap-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={open && active === t.id}
              aria-controls={panelId}
              onClick={() => choose(t.id)}
              className={`-mb-px border-b-[3px] px-2 py-2 text-sm font-bold ${
                open && active === t.id ? 'border-accent-ink text-accent-ink' : 'border-transparent text-ink-muted hover:text-ink'
              }`}
            >
              {t.label}
            </button>
          ))}
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
