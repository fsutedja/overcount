import type { SolutionStep } from '../types/problem'
import { ce } from '../lib/grade'
import { fillTemplate } from '../lib/template'
import { StepCarousel } from './StepCarousel'
import { StepIcon } from './StepIcon'
import { Tex } from './Tex'

/** A step's value as LaTeX, e.g. "56", or null when it is already just a number. */
function valueOf(latex: string): string | null {
  // A step that is already just a number ("56") needs no "= 56".
  if (/^\s*\{*-?\d+\}*\s*$/.test(latex)) return null
  const value = ce.parse(latex).evaluate()
  return Number.isFinite(value.re) ? value.latex : null
}

/**
 * "Show solution": the worked answer with this problem's numbers, one step at a time with ‹ ›
 * arrows like Help, each with its math-symbol icon (DESIGN.md, D2). It shows the computation (C(8,3) = 56, 56 × 15 = 840); the
 * reasoning lives in Help, so the two never repeat each other.
 */
export function SolutionSteps({ steps, vars }: { steps: SolutionStep[]; vars: Record<string, string> }) {
  const slides = steps.map((step, index) => {
    const latex = fillTemplate(step.latex, vars)
    const value = valueOf(latex)
    return (
      <div key={index} className="h-full rounded-xl border border-border bg-card-sunken px-4 py-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <StepIcon kind={step.kind} />
          <span className="font-bold">
            {index + 1}. {step.title}
          </span>
        </div>
        <Tex latex={value ? `${latex} = ${value}` : latex} display className="block overflow-x-auto [&_.katex-display]:my-2" />
      </div>
    )
  })
  const captions = steps.map((_, i) => (i === steps.length - 1 ? `Step ${i + 1} of ${steps.length}: the answer` : `Step ${i + 1} of ${steps.length}`))
  return <StepCarousel label="Worked solution" slides={slides} captions={captions} />
}
