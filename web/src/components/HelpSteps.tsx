import { useState } from 'react'
import { formatValue } from '../lib/grade'
import type { HelpCheck, HelpStep } from '../types/problem'
import { RichText } from './RichText'
import { StepIcon } from './StepIcon'
import { Tex } from './Tex'

interface HelpStepsProps {
  steps: HelpStep[]
  check: HelpCheck
}

/**
 * Help (CLAUDE.md, Product): numbered "why" steps shown one at a time in place, with ‹ › arrows
 * to move between them; the last slide is a check with the smallest numbers. It explains the
 * reasoning in letters and never fills in this problem's blanks; the worked answer with numbers
 * is "Show solution". The slide uses the D2 step-card style.
 */
export function HelpSteps({ steps, check }: HelpStepsProps) {
  const [index, setIndex] = useState(0)
  const total = steps.length + 1 // the steps, then the small-numbers check
  const go = (next: number) => setIndex(Math.min(total - 1, Math.max(0, next)))
  const step = steps[index]

  return (
    <div
      role="group"
      aria-roledescription="carousel"
      aria-label="Help steps"
      onKeyDown={(event) => {
        if (event.key === 'ArrowRight') go(index + 1)
        if (event.key === 'ArrowLeft') go(index - 1)
      }}
    >
      <div className="flex items-stretch gap-2">
        <Arrow direction="previous" disabled={index === 0} onClick={() => go(index - 1)} />
        <div className="min-w-0 flex-1" aria-live="polite">
          {step ? (
            <div className="h-full rounded-xl border border-border bg-card-sunken px-4 py-3">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <StepIcon kind={step.kind} />
                <span className="font-bold">
                  {index + 1}. {step.title}
                </span>
              </div>
              <p className="mt-2 leading-relaxed">
                <RichText text={step.text} />
              </p>
              {step.latex && <Tex latex={step.latex} display className="block overflow-x-auto [&_.katex-display]:my-2" />}
            </div>
          ) : (
            <SmallCase check={check} />
          )}
        </div>
        <Arrow direction="next" disabled={index === total - 1} onClick={() => go(index + 1)} />
      </div>
      <p className="mt-2 text-center text-sm text-ink-muted">
        {step ? `Step ${index + 1} of ${steps.length}` : 'Check with small numbers'}
      </p>
    </div>
  )
}

function Arrow({ direction, disabled, onClick }: { direction: 'previous' | 'next'; disabled: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={direction === 'previous' ? 'Previous step' : 'Next step'}
      className="shrink-0 self-center rounded-full border-2 border-accent-ink px-2.5 py-1 text-lg font-bold text-accent-ink hover:bg-accent-soft disabled:border-border disabled:text-ink-muted disabled:opacity-50 disabled:hover:bg-transparent"
    >
      <span aria-hidden="true">{direction === 'previous' ? '‹' : '›'}</span>
    </button>
  )
}

function SmallCase({ check }: { check: HelpCheck }) {
  const numbers = Object.entries(check.vars)
    .map(([name, value]) => `${name} = ${value}`)
    .join(',\\ ')
  const answer = formatValue(check.answer)
  const steps = [check.filled, check.worked, answer].filter((part, i, all) => i === 0 || part !== all[i - 1])
  return (
    <div className="h-full rounded-xl border border-border bg-accent-soft px-4 py-3 text-accent-ink">
      <p className="font-bold">
        Check with small numbers: <Tex latex={numbers} />
      </p>
      <Tex latex={`\\begin{aligned}${steps.map((part, i) => (i === 0 ? `& ${part}` : `&= ${part}`)).join(' \\\\ ')}\\end{aligned}`} display className="block overflow-x-auto [&_.katex-display]:my-2" />
      {check.outcomes && (
        <p className="text-sm">
          The {check.outcomes.length} that count: {check.outcomes.join(' · ')}
        </p>
      )}
      <p className="mt-1 text-sm">Now do the same with this problem's numbers.</p>
    </div>
  )
}
