import { formatValue } from '../lib/grade'
import type { HelpCheck, HelpStep } from '../types/problem'
import { RichText } from './RichText'
import { StepIcon } from './StepIcon'
import { Tex } from './Tex'

interface HelpStepsProps {
  steps: HelpStep[]
  check: HelpCheck
  /** How many steps are showing; when it equals steps.length, the small-case check shows too. */
  revealed: number
  onNext: () => void
  onSkip: () => void
}

/**
 * Help, part one (CLAUDE.md, Product): numbered "why" steps revealed one at a time, then a check
 * with the smallest numbers. The skeleton with blanks follows (rendered by the caller).
 * Cards use the solution-step style (DESIGN.md, D2).
 */
export function HelpSteps({ steps, check, revealed, onNext, onSkip }: HelpStepsProps) {
  const done = revealed >= steps.length
  return (
    <div className="space-y-3">
      <ol className="space-y-3" aria-live="polite">
        {steps.slice(0, revealed).map((step, index) => (
          <li key={index} className="rounded-xl border border-border bg-card-sunken px-4 py-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <StepIcon kind={step.kind} />
              <span className="font-bold">
                {index + 1}. {step.title}
              </span>
            </div>
            <p className="mt-2 leading-relaxed">
              <RichText text={step.text} />
            </p>
            {step.latex && <Tex latex={step.latex} display className="block [&_.katex-display]:my-2" />}
          </li>
        ))}
        {done && <SmallCase check={check} />}
      </ol>
      {!done && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <button type="button" onClick={onNext} className="rounded-lg border-2 border-accent-ink px-4 py-1.5 font-bold text-accent-ink hover:bg-accent-soft">
            {revealed === 0 ? 'Show the first step' : 'Next step'}
          </button>
          <button type="button" onClick={onSkip} className="text-sm font-bold text-ink-muted underline-offset-4 hover:underline">
            Skip to the blanks
          </button>
          <span className="text-sm text-ink-muted">
            {revealed} of {steps.length} steps
          </span>
        </div>
      )}
    </div>
  )
}

function SmallCase({ check }: { check: HelpCheck }) {
  const numbers = Object.entries(check.vars)
    .map(([name, value]) => `${name} = ${value}`)
    .join(',\\ ')
  const answer = formatValue(check.answer)
  const steps = [check.filled, check.worked, answer].filter((part, i, all) => i === 0 || part !== all[i - 1])
  return (
    <li className="rounded-xl border border-border bg-accent-soft px-4 py-3 text-accent-ink">
      <p className="font-bold">
        Check with small numbers: <Tex latex={numbers} />
      </p>
      <Tex latex={steps.join(' = ')} display className="block [&_.katex-display]:my-2" />
      {check.outcomes && (
        <p className="text-sm">
          The {check.outcomes.length} that count: {check.outcomes.join(' · ')}
        </p>
      )}
      <p className="mt-1 text-sm">Now do the same with this problem's numbers.</p>
    </li>
  )
}
