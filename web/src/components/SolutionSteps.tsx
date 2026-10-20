import type { SolutionStep } from '../types/problem'
import { fillTemplate } from '../lib/template'
import { StepIcon } from './StepIcon'
import { Tex } from './Tex'

/** The read-only worked solution, one step per row with its math-symbol icon. */
export function SolutionSteps({ steps, vars }: { steps: SolutionStep[]; vars: Record<string, string> }) {
  return (
    <ol className="space-y-3">
      {steps.map((step, index) => (
        <li key={index} className="rounded-xl border border-border bg-card px-4 py-3">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <StepIcon kind={step.kind} />
            <span className="font-bold">{step.title}</span>
            <Tex latex={fillTemplate(step.latex, vars)} className="text-lg" />
          </div>
          <p className="mt-2 text-ink-muted">{fillTemplate(step.explanation, vars)}</p>
        </li>
      ))}
    </ol>
  )
}
