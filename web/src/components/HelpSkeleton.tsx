import { Fragment, useEffect, useRef } from 'react'
import type { Skeleton } from '../types/problem'

interface HelpSkeletonProps {
  skeleton: Skeleton
  values: Record<string, string>
  wrongSlots: string[]
  onChange: (slot: string, value: string) => void
  onSubmit: () => void
}

/** Splits a display template like "C([a], [b])" into text and slot tokens. */
function tokens(display: string) {
  return display.split(/(\[\w+\])/).filter(Boolean).map((token) => {
    const slot = token.match(/^\[(\w+)\]$/)?.[1]
    return slot ? { slot } : { text: token }
  })
}

/**
 * The Help view: the whole answer's structure on one line, e.g. C( _ , _ ) × C( _ , _ ),
 * with each group's label underneath and a hint inside each box. The learner fills in numbers.
 */
export function HelpSkeleton({ skeleton, values, wrongSlots, onChange, onSubmit }: HelpSkeletonProps) {
  const firstInput = useRef<HTMLInputElement>(null)
  useEffect(() => firstInput.current?.focus(), [])
  let firstSlot = true

  return (
    <div className="flex flex-wrap items-start gap-x-3 gap-y-4 text-2xl">
      {skeleton.parts.map((part, index) => {
        if ('op' in part) {
          return (
            <span key={index} className="pt-1.5 font-bold" aria-label={part.op.display === '×' ? 'times' : part.op.display}>
              {part.op.display}
            </span>
          )
        }
        const { label, display } = part.group
        return (
          <span key={index} role="group" aria-label={label} className="inline-flex flex-col items-center">
            <span className="flex items-center gap-1">
              {tokens(display).map((token, i) => {
                if ('text' in token) return <Fragment key={i}>{token.text}</Fragment>
                const slot = token.slot
                const hint = skeleton.slots[slot]?.hint ?? ''
                const wrong = wrongSlots.includes(slot)
                const isFirst = firstSlot
                firstSlot = false
                return (
                  <input
                    key={i}
                    ref={isFirst ? firstInput : undefined}
                    value={values[slot] ?? ''}
                    onChange={(event) => onChange(slot, event.target.value)}
                    onKeyDown={(event) => event.key === 'Enter' && onSubmit()}
                    placeholder={hint}
                    aria-label={`${label}: ${hint}`}
                    aria-invalid={wrong}
                    inputMode="decimal"
                    autoComplete="off"
                    className={`w-16 rounded-lg border-2 bg-card px-1 py-1 text-center text-xl font-bold placeholder:text-sm placeholder:font-normal placeholder:text-ink-muted ${
                      wrong ? 'border-wrong-ink bg-wrong-bg text-wrong-ink' : 'border-accent text-ink'
                    }`}
                  />
                )
              })}
            </span>
            <span className="mt-1 text-sm text-ink-muted">{label}</span>
          </span>
        )
      })}
    </div>
  )
}
