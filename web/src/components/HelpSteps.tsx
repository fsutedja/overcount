import { formatValue } from '../lib/grade'
import type { HelpCheck, HelpStep } from '../types/problem'
import { RichText } from './RichText'
import { StepCarousel } from './StepCarousel'
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
  const slides = [
    ...steps.map((step, index) => (
      <div key={index} className="h-full rounded-xl border border-border bg-card-sunken px-4 py-3">
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
    )),
    <SmallCase key="check" check={check} />,
  ]
  const captions = [...steps.map((_, i) => `Step ${i + 1} of ${steps.length}`), 'Check with small numbers']
  return <StepCarousel label="Help steps" slides={slides} captions={captions} />
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
