import { useState } from 'react'
import type { Instance, Problem } from '../types/problem'
import { formatValue, gradeLatex, type GradeResult } from '../lib/grade'
import { MathInput } from './MathInput'

interface ProblemViewProps {
  problem: Problem
  instance: Instance
}

/** Fills {{var}} placeholders with the instance's numbers. */
function fillTemplate(text: string, vars: Record<string, string>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (match, name: string) => vars[name] ?? match)
}

export function ProblemView({ problem, instance }: ProblemViewProps) {
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState<GradeResult | null>(null)
  const solved = result?.kind === 'correct'

  const check = () => setResult(gradeLatex(answer, instance.values.final))

  return (
    <article className="mx-auto max-w-2xl px-4 py-8">
      <section className="overflow-hidden rounded-xl border border-border bg-card" aria-labelledby="problem-title">
        <div
          aria-hidden="true"
          className="h-2 bg-card [background-image:radial-gradient(circle_at_6px_0,var(--bg)_4px,transparent_4.5px)] [background-size:12px_8px]"
        />
        <div className="px-5 pb-5 pt-2">
          <p className="text-xs tracking-wide text-ink-muted uppercase">
            {problem.difficulty} · {problem.tags.contexts.map((c) => c.split('-')[0]).join(', ')}
          </p>
          <h1 id="problem-title" className="mt-1 text-xl font-bold">
            {problem.title}
          </h1>
          <p className="mt-2 text-lg leading-relaxed">{fillTemplate(problem.statement, instance.vars)}</p>
        </div>
      </section>

      <section className="mt-6 rounded-xl border-2 border-accent bg-card p-5" aria-labelledby="final-label">
        <h2 id="final-label" className="font-bold">
          Final answer <span className="font-normal text-ink-muted">· {problem.final.prompt.toLowerCase()}</span>
        </h2>
        <p className="mt-1 text-sm text-ink-muted">
          Type an expression, not a number. Try <kbd className="font-bold">C(</kbd> or{' '}
          <kbd className="font-bold">choose</kbd> for a binomial, and <kbd className="font-bold">/</kbd> for a fraction.
        </p>
        <div className="mt-3">
          <MathInput
            label={problem.final.prompt}
            invalid={result?.kind === 'wrong'}
            onChange={(latex) => {
              setAnswer(latex)
              if (!solved) setResult(null)
            }}
            onSubmit={check}
          />
        </div>

        <div aria-live="polite" className="mt-3">
          {result?.kind === 'invalid' && <p className="text-sm text-ink-muted">{result.message}</p>}
          {result?.kind === 'wrong' && (
            <p className="rounded-lg bg-wrong-bg px-3 py-2 text-wrong-ink">
              <span className="font-bold">✗ Not quite.</span> Check whether order matters, and how many you pick from
              each group.
            </p>
          )}
          {solved && (
            <p className="rounded-lg bg-correct-bg px-4 py-3 text-correct-ink">
              <span className="font-bold">✓ Correct.</span> That's {formatValue(instance.values.final)}.
            </p>
          )}
        </div>

        {!solved && (
          <button
            type="button"
            onClick={check}
            className="mt-4 rounded-lg bg-accent-ink px-4 py-2 font-bold text-on-accent hover:opacity-90"
          >
            Check answer
          </button>
        )}
      </section>
    </article>
  )
}
