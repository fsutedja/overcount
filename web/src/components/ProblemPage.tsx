import { useState } from 'react'
import type { Instance, Problem } from '../types/problem'
import { gradeFreeAnswer, gradeSkeleton, skeletonLatex, type AnswerResult, type SkeletonResult } from '../lib/answer'
import { createAttempt, recordAttempt, type HelpLevel } from '../lib/attempts'
import { formatValue } from '../lib/grade'
import { fillTemplate } from '../lib/template'
import { HelpSkeleton } from './HelpSkeleton'
import { MathInput } from './MathInput'
import { SolutionSteps } from './SolutionSteps'
import { Tex } from './Tex'

interface ProblemPageProps {
  problem: Problem
  instance: Instance
}

/**
 * Answer-first problem page (PLAN.md, DESIGN.md D2): the problem stays pinned on the left; on the
 * right the learner answers freely, can open Help for a one-line skeleton, and can finally see
 * the worked solution.
 */
export function ProblemPage({ problem, instance }: ProblemPageProps) {
  const [freeLatex, setFreeLatex] = useState('')
  const [freeResult, setFreeResult] = useState<AnswerResult | null>(null)
  const [helpOpen, setHelpOpen] = useState(false)
  const [slotValues, setSlotValues] = useState<Record<string, string>>({})
  const [skeletonResult, setSkeletonResult] = useState<SkeletonResult | null>(null)
  const [skeletonMisses, setSkeletonMisses] = useState(0)
  const [solutionShown, setSolutionShown] = useState(false)
  const [solvedLatex, setSolvedLatex] = useState<string | null>(null)
  /** Highest help used so far; going back to the free box doesn't lower it. */
  const [helpLevel, setHelpLevel] = useState<HelpLevel>(0)

  const solved = solvedLatex !== null

  const record = (result: AnswerResult) => {
    if (result.kind === 'invalid') return
    recordAttempt(
      createAttempt({
        problem_id: problem.id,
        family_id: problem.family_id,
        instance_key: instance.key,
        help_level: helpLevel,
        correct: result.kind === 'correct',
        mistake_tags: result.kind === 'wrong' && result.mistakeTag ? [result.mistakeTag] : [],
      }),
    )
  }

  const checkFree = () => {
    const result = gradeFreeAnswer(freeLatex, problem, instance)
    setFreeResult(result)
    record(result)
    if (result.kind === 'correct') setSolvedLatex(freeLatex)
  }

  const checkSkeleton = () => {
    const result = gradeSkeleton(slotValues, problem, instance)
    setSkeletonResult(result)
    record(result)
    if (result.kind === 'wrong') setSkeletonMisses((n) => n + 1)
    if (result.kind === 'correct') setSolvedLatex(skeletonLatex(problem.answer.skeleton, slotValues))
  }

  const openHelp = () => {
    setHelpOpen(true)
    setHelpLevel((level) => (level < 1 ? 1 : level))
  }

  const showSolution = () => {
    setSolutionShown(true)
    if (!solved) setHelpLevel(2)
  }

  return (
    <article className="mx-auto max-w-5xl px-4 py-6 md:grid md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] md:items-start md:gap-6 md:py-8">
      <div className="md:sticky md:top-6">
        <h2 className="mb-3 font-bold">Problem</h2>
        <section className="overflow-hidden rounded-xl border border-border bg-card" aria-labelledby="problem-title">
          <div
            aria-hidden="true"
            className="h-2 bg-card [background-image:radial-gradient(circle_at_6px_0,var(--bg)_4px,transparent_4.5px)] [background-size:12px_8px]"
          />
          <div className="px-5 pt-2 pb-5">
            <p className="text-xs tracking-wide text-ink-muted uppercase">
              {problem.difficulty} · {problem.kind} ·{' '}
              {problem.tags.contexts.map((c) => c.split('-')[0]).join(', ')}
            </p>
            <h1 id="problem-title" className="mt-1 text-xl font-bold">
              {problem.title}
            </h1>
            <p className="mt-2 text-lg leading-relaxed">{fillTemplate(problem.statement, instance.vars)}</p>
          </div>
        </section>
      </div>

      <div className="mt-6 space-y-6 md:mt-0">
        <section aria-labelledby="answer-heading">
          <h2 id="answer-heading" className="mb-3 font-bold">
            Your answer
          </h2>
          <div className="rounded-xl border-2 border-accent bg-card p-5">
            <p className="font-bold">{problem.answer.prompt}</p>

            {solved ? (
              <div className="mt-3">
                <Tex latex={solvedLatex} className="text-xl" />
                <p className="mt-3 rounded-lg bg-correct-bg px-4 py-3 text-correct-ink">
                  <span className="font-bold">✓ Correct.</span> That's {formatValue(instance.values.answer)}.
                </p>
              </div>
            ) : helpOpen ? (
              <div className="mt-1">
                <p className="text-sm text-ink-muted">Here's the structure. Fill in the numbers.</p>
                <div className="mt-4">
                  <HelpSkeleton
                    skeleton={problem.answer.skeleton}
                    values={slotValues}
                    wrongSlots={skeletonResult?.wrongSlots ?? []}
                    onChange={(slot, value) => {
                      setSlotValues((current) => ({ ...current, [slot]: value }))
                      setSkeletonResult(null)
                    }}
                    onSubmit={checkSkeleton}
                  />
                </div>
                <Feedback result={skeletonResult} fallback="The highlighted boxes don't match. Reread the problem for those numbers." />
              </div>
            ) : (
              <div className="mt-1">
                <p className="text-sm text-ink-muted">
                  Type an expression. Try <kbd className="font-bold">C(</kbd> or <kbd className="font-bold">choose</kbd> for a
                  binomial and <kbd className="font-bold">/</kbd> for a fraction.
                </p>
                <div className="mt-3">
                  <MathInput
                    label={problem.answer.prompt}
                    invalid={freeResult?.kind === 'wrong'}
                    autoFocus
                    onChange={(latex) => {
                      setFreeLatex(latex)
                      setFreeResult(null)
                    }}
                    onSubmit={checkFree}
                  />
                </div>
                <Feedback result={freeResult} fallback="Try again, or open Help to see the structure." />
              </div>
            )}

            {!solved && (
              <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
                <button
                  type="button"
                  onClick={helpOpen ? checkSkeleton : checkFree}
                  className="rounded-lg bg-accent-ink px-4 py-2 font-bold text-on-accent hover:opacity-90"
                >
                  Check answer
                </button>
                {!helpOpen && (
                  <button type="button" onClick={openHelp} className="font-bold text-accent-ink underline-offset-4 hover:underline">
                    Help
                  </button>
                )}
                {helpOpen && (
                  <button
                    type="button"
                    onClick={() => setHelpOpen(false)}
                    className="text-sm font-bold text-ink-muted underline-offset-4 hover:underline"
                  >
                    Type the full expression instead
                  </button>
                )}
                {helpOpen && skeletonMisses >= 1 && !solutionShown && (
                  <button type="button" onClick={showSolution} className="text-sm font-bold text-ink-muted underline-offset-4 hover:underline">
                    Show solution
                  </button>
                )}
              </div>
            )}
            {solved && !solutionShown && (
              <button
                type="button"
                onClick={showSolution}
                className="mt-4 text-sm font-bold text-accent-ink underline-offset-4 hover:underline"
              >
                See the worked solution
              </button>
            )}
          </div>
        </section>

        {solutionShown && (
          <section aria-labelledby="solution-heading">
            <h2 id="solution-heading" className="mb-3 font-bold">
              Solution
            </h2>
            <SolutionSteps steps={problem.solution} vars={instance.vars} />
          </section>
        )}
      </div>
    </article>
  )
}

function Feedback({ result, fallback }: { result: AnswerResult | null; fallback: string }) {
  return (
    <div aria-live="polite">
      {result?.kind === 'invalid' && <p className="mt-3 text-sm text-ink-muted">{result.message}</p>}
      {result?.kind === 'wrong' && (
        <p className="mt-3 rounded-lg bg-wrong-bg px-3 py-2 text-wrong-ink">
          <span className="font-bold">✗ Not quite.</span> {result.feedback ?? fallback}
        </p>
      )}
    </div>
  )
}
