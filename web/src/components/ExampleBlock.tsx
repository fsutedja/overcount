import { useState } from 'react'
import type { Instance, Problem } from '../types/problem'
import { OutcomeVisual } from './OutcomeVisual'

/**
 * Which example pair is showing, per problem and set of numbers. Kept in memory so going back to
 * a problem shows the same pair; the pairs themselves are precomputed in the bank.
 */
const shownPair = new Map<string, number>()

/**
 * "What does one outcome look like?": a diagram of an outcome that counts, then one that counts
 * (✅) and one that doesn't (❌), each with a reason. "Show another example" steps through more
 * checked pairs; none of them reveal the answer.
 */
export function ExampleBlock({ problem, instance }: { problem: Problem; instance: Instance }) {
  const key = `${problem.id}|${instance.key}`
  const [index, setIndex] = useState(() => shownPair.get(key) ?? 0)
  const { pairs, pool, captions } = instance.example
  const pair = pairs[index % pairs.length]

  const another = () => {
    const next = (index + 1) % pairs.length
    shownPair.set(key, next)
    setIndex(next)
  }

  return (
    <div className="space-y-3">
      <OutcomeVisual type={problem.visual.type} side={pair.yes} pool={pool} captions={captions} />
      {problem.visual.legend && <p className="text-center text-sm text-ink-muted">{problem.visual.legend}</p>}
      <ul className="space-y-1.5" aria-live="polite">
        <li className="rounded-lg bg-correct-bg px-3 py-1.5 text-correct-ink">
          <span aria-label="counts">✅</span> <span className="font-bold">{pair.yes.text}</span>{' '}
          <span>({pair.yes.reason})</span>
        </li>
        <li className="rounded-lg bg-wrong-bg px-3 py-1.5 text-wrong-ink">
          <span aria-label="doesn't count">❌</span> <span className="font-bold">{pair.no.text}</span>{' '}
          <span>({pair.no.reason})</span>
        </li>
      </ul>
      {pairs.length > 1 && (
        <button type="button" onClick={another} className="text-sm font-bold text-accent-ink underline-offset-4 hover:underline">
          Show another example ({(index % pairs.length) + 1} of {pairs.length})
        </button>
      )}
    </div>
  )
}
