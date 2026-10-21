import { useState } from 'react'
import type { Instance, Problem } from '../types/problem'
import { gradeFreeAnswer, gradeSkeleton, skeletonLatex, type AnswerResult, type SkeletonResult } from '../lib/answer'
import { createAttempt, recordAttempt, recordedAttempts, type HelpLevel } from '../lib/attempts'
import { NUDGE_AFTER_WRONG, problemProgress } from '../lib/progress'
import { formatValue } from '../lib/grade'
import { fillTemplate } from '../lib/template'
import { HelpSkeleton } from './HelpSkeleton'
import { HelpSteps } from './HelpSteps'
import { MathInput } from './MathInput'
import { ProblemCardTabs } from './ProblemCardTabs'
import { SolutionSteps } from './SolutionSteps'
import { Tex } from './Tex'
import { TryDots } from './TryDots'

interface ProblemPageProps {
  problem: Problem
  instance: Instance
  /** Set when opened from that method's Practice tab: the method pill shows at once. */
  fromMethod?: string | null
  /** Switches to another number set of the same problem (the ↻ button, DESIGN.md D9). */
  onNewNumbers?: () => void
}

/**
 * Answer-first problem page (CLAUDE.md, Product): the problem stays pinned on the left; on the
 * right the learner answers freely, can fill in the blanks of a one-line skeleton, ask for Help
 * (numbered why-steps, revealed one at a time), and finally see the worked solution.
 */
export function ProblemPage({ problem, instance, fromMethod = null, onNewNumbers }: ProblemPageProps) {
  const [freeLatex, setFreeLatex] = useState('')
  const [freeResult, setFreeResult] = useState<AnswerResult | null>(null)
  /** The skeleton with blanks is open (instead of the free answer box). */
  const [blanksOpen, setBlanksOpen] = useState(false)
  /** Help (the why-steps) has been asked for. */
  const [helpShown, setHelpShown] = useState(false)
  const [slotValues, setSlotValues] = useState<Record<string, string>>({})
  const [skeletonResult, setSkeletonResult] = useState<SkeletonResult | null>(null)
  const [skeletonMisses, setSkeletonMisses] = useState(0)
  const [solutionShown, setSolutionShown] = useState(false)
  const [solvedLatex, setSolvedLatex] = useState<string | null>(null)
  /** Highest help used so far; going back to the free box doesn't lower it. */
  const [helpLevel, setHelpLevel] = useState<HelpLevel>(0)

  const solved = solvedLatex !== null
  /** Tries on this problem so far (across visits and number sets), for the dots and Help nudge. */
  const [progress, setProgress] = useState(() => problemProgress(recordedAttempts(), problem.id))
  // Naming the method can give the problem away, so outside method practice its tab appears
  // only once the learner has tried (DESIGN.md, D6 and D7).
  const showMethods =
    (fromMethod !== null && problem.tags.methods.includes(fromMethod)) || progress.tries.some((right) => !right) || solved
  const nudgeBlanks = !solved && !blanksOpen && progress.status === 'tried' && progress.wrong >= NUDGE_AFTER_WRONG

  const record = (result: AnswerResult, answer: string) => {
    if (result.kind === 'invalid') return
    const saved = recordAttempt(
      createAttempt({
        problem_id: problem.id,
        family_id: problem.family_id,
        instance_key: instance.key,
        help_level: helpLevel,
        correct: result.kind === 'correct',
        answer,
        mistake_tags: result.kind === 'wrong' && result.mistakeTag ? [result.mistakeTag] : [],
      }),
    )
    if (saved) setProgress(problemProgress(recordedAttempts(), problem.id))
  }

  const checkFree = () => {
    const result = gradeFreeAnswer(freeLatex, problem, instance)
    setFreeResult(result)
    record(result, freeLatex)
    if (result.kind === 'correct') setSolvedLatex(freeLatex)
  }

  const checkSkeleton = () => {
    const result = gradeSkeleton(slotValues, problem, instance)
    setSkeletonResult(result)
    record(result, skeletonLatex(problem.answer.skeleton, slotValues))
    if (result.kind === 'wrong') setSkeletonMisses((n) => n + 1)
    if (result.kind === 'correct') setSolvedLatex(skeletonLatex(problem.answer.skeleton, slotValues))
  }

  const openBlanks = () => {
    setBlanksOpen(true)
    setHelpLevel((level) => (level < 1 ? 1 : level))
  }

  const openHelp = () => setHelpShown(true)

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
            <div className="mt-1 flex items-start justify-between gap-3">
              <h1 id="problem-title" className="text-xl font-bold">
                {problem.title}
              </h1>
              {onNewNumbers && (
                <button
                  type="button"
                  onClick={onNewNumbers}
                  title="New numbers"
                  aria-label="New numbers"
                  className="shrink-0 rounded-lg px-1.5 text-xl leading-7 font-bold text-accent-ink hover:bg-card-sunken"
                >
                  <span aria-hidden="true">↻</span>
                </button>
              )}
            </div>
            <p className="mt-2 text-lg leading-relaxed">{fillTemplate(problem.statement, instance.vars)}</p>
            <ProblemCardTabs
              problem={problem}
              instance={instance}
              methods={
                !showMethods
                  ? []
                  : fromMethod
                    ? [fromMethod, ...problem.tags.methods.filter((m) => m !== fromMethod)]
                    : problem.tags.methods
              }
            />
          </div>
        </section>
      </div>

      <div className="mt-6 space-y-6 md:mt-0">
        <section aria-labelledby="answer-heading">
          <h2 id="answer-heading" className="mb-3 font-bold">
            Your answer
          </h2>
          <div className="rounded-xl border-2 border-accent bg-card p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-x-3">
              <p className="font-bold">{problem.answer.prompt}</p>
              {(progress.tries.length > 0 || !solved) && (
                <p className="flex items-center gap-2 text-sm text-ink-muted">
                  <TryDots tries={progress.tries} next={progress.status === 'tried' || progress.status === 'new'} />
                  {progress.status === 'tried' || progress.status === 'new' ? `try ${progress.tries.length + 1}` : null}
                </p>
              )}
            </div>

            {solved ? (
              <div className="mt-3">
                <Tex latex={solvedLatex} className="text-xl" />
                <p className="mt-3 rounded-lg bg-correct-bg px-4 py-3 text-correct-ink">
                  <span className="font-bold">✓ Correct.</span> That's {formatValue(instance.values.answer)}.
                </p>
              </div>
            ) : blanksOpen ? (
              <div className="mt-1">
                <p className="text-sm text-ink-muted">Here's the structure. Fill in the numbers.</p>
                <div className="mt-4">
                  <HelpSkeleton
                    skeleton={problem.answer.skeleton}
                    wrongSlots={skeletonResult?.wrongSlots ?? []}
                    onChange={(slot, value) => {
                      setSlotValues((current) => ({ ...current, [slot]: value }))
                      setSkeletonResult(null)
                    }}
                    onSubmit={checkSkeleton}
                  />
                </div>
                <Feedback result={skeletonResult} fallback="The shaded boxes don't match. Reread the problem for those numbers." />
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
                <Feedback result={freeResult} fallback="Try again, or fill in the blanks to see the structure." />
              </div>
            )}

            {!solved && (
              <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
                <button
                  type="button"
                  onClick={blanksOpen ? checkSkeleton : checkFree}
                  className="rounded-lg bg-accent-ink px-4 py-2 font-bold text-on-accent hover:opacity-90"
                >
                  Check answer
                </button>
                {!blanksOpen && (
                  <button type="button" onClick={openBlanks} className="font-bold text-accent-ink underline-offset-4 hover:underline">
                    Fill in the blanks
                  </button>
                )}
                {nudgeBlanks && <span className="text-sm text-ink-muted">← stuck? fill in the blanks</span>}
                {blanksOpen && !helpShown && (
                  <button type="button" onClick={openHelp} className="font-bold text-accent-ink underline-offset-4 hover:underline">
                    Help
                  </button>
                )}
                {blanksOpen && (
                  <button
                    type="button"
                    onClick={() => setBlanksOpen(false)}
                    className="text-sm font-bold text-ink-muted underline-offset-4 hover:underline"
                  >
                    Type the full expression instead
                  </button>
                )}
                {blanksOpen && skeletonMisses >= 1 && !solutionShown && (
                  <button type="button" onClick={showSolution} className="text-sm font-bold text-ink-muted underline-offset-4 hover:underline">
                    Show solution
                  </button>
                )}
              </div>
            )}
            {!solved && blanksOpen && helpShown && (
              <div className="mt-5 border-t border-border pt-4">
                <h3 className="mb-3 font-bold">Help: why it works</h3>
                <HelpSteps steps={problem.help_steps} check={problem.help_check} />
              </div>
            )}
            {solutionShown && (
              <section aria-labelledby="solution-heading" className="mt-5 border-t border-border pt-4">
                <h3 id="solution-heading" className="mb-3 font-bold">
                  Solution
                </h3>
                <SolutionSteps steps={problem.solution} vars={instance.vars} />
              </section>
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
