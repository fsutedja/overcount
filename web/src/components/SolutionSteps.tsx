import type { SolutionStep } from '../types/problem'
import { ce } from '../lib/grade'
import { fillTemplate } from '../lib/template'
import { StepIcon } from './StepIcon'
import { Tex } from './Tex'

/** A step's value as LaTeX, e.g. "56", or null when it is already just a number. */
function valueOf(latex: string): string | null {
  const parsed = ce.parse(latex)
  if (!parsed.isValid) return null
  const value = parsed.evaluate()
  if (!Number.isFinite(value.re) || value.latex === parsed.latex) return null
  return value.latex
}

/**
 * "Show solution": the worked answer with this problem's numbers, one step per row with its
 * math-symbol icon (DESIGN.md, D2). It shows the computation (C(8,3) = 56, 56 × 15 = 840); the
 * reasoning lives in Help, so the two never repeat each other.
 */
export function SolutionSteps({ steps, vars }: { steps: SolutionStep[]; vars: Record<string, string> }) {
  return (
    <ol className="space-y-3">
      {steps.map((step, index) => {
        const latex = fillTemplate(step.latex, vars)
        const value = valueOf(latex)
        return (
          <li key={index} className="rounded-xl border border-border bg-card px-4 py-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <StepIcon kind={step.kind} />
              <span className="font-bold">{step.title}</span>
            </div>
            <Tex latex={value ? `${latex} = ${value}` : latex} display className="block [&_.katex-display]:my-2" />
          </li>
        )
      })}
    </ol>
  )
}
