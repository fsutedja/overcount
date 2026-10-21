import { useId, useState } from 'react'
import { loadShowExample, saveShowExample } from '../lib/exampleToggle'
import { fillTemplate } from '../lib/template'
import type { Instance, Problem } from '../types/problem'
import { OutcomeVisual } from './OutcomeVisual'

/**
 * "What does one outcome look like?": a diagram of an outcome that counts, then one that counts
 * (✅) and one that doesn't (❌), each with a reason. Open by default; the toggle is remembered.
 */
export function ExampleBlock({ problem, instance }: { problem: Problem; instance: Instance }) {
  const [open, setOpen] = useState(loadShowExample)
  const bodyId = useId()
  const { example } = instance

  const toggle = () => {
    setOpen(!open)
    saveShowExample(!open)
  }

  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        aria-controls={bodyId}
        className="flex items-center gap-1.5 font-bold text-accent-ink"
      >
        <span aria-hidden="true">{open ? '▾' : '▸'}</span> Example
      </button>
      {open && (
        <div id={bodyId} className="mt-3 space-y-3">
          <OutcomeVisual type={problem.visual.type} example={example} />
          <ul className="space-y-1.5">
            <li className="rounded-lg bg-correct-bg px-3 py-1.5 text-correct-ink">
              <span aria-label="counts">✅</span> <span className="font-bold">{example.yes.text}</span>{' '}
              <span>({fillTemplate(problem.example.yes_reason, instance.vars)})</span>
            </li>
            <li className="rounded-lg bg-wrong-bg px-3 py-1.5 text-wrong-ink">
              <span aria-label="doesn't count">❌</span> <span className="font-bold">{example.no.text}</span>{' '}
              <span>({fillTemplate(problem.example.no_reason, instance.vars)})</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  )
}
