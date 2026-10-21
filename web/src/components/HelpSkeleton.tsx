import { useEffect, useRef } from 'react'
import type { MathfieldElement } from 'mathlive'
import type { Skeleton } from '../types/problem'
import { Tex } from './Tex'

interface HelpSkeletonProps {
  skeleton: Skeleton
  wrongSlots: string[]
  onChange: (slot: string, value: string) => void
  onSubmit: () => void
}

const slotIds = (latex: string) => [...latex.matchAll(/\[(\w+)\]/g)].map((m) => m[1])

/** "\binom{[a]}{[b]}" → "\binom{\placeholder[a]{}}{\placeholder[b]{}}": empty boxes to fill in. */
const withBlanks = (latex: string) => latex.replace(/\[(\w+)\]/g, (_, slot: string) => `\\placeholder[${slot}]{}`)

/**
 * A wrong blank is only shaded with the wrong (berry) tint (DESIGN.md): MathLive's own marking
 * (outline glow, a slash across the box, a coloured digit) is turned off. Its styles live inside
 * each field's shadow DOM, so this sheet is adopted there.
 */
const wrongBlankStyle = (() => {
  if (typeof CSSStyleSheet === 'undefined') return null
  const sheet = new CSSStyleSheet()
  sheet.replaceSync(`
    .ML__incorrectPromptBox { outline: 1px solid rgb(172, 172, 172); box-shadow: none; background-color: var(--wrong-bg); }
    .ML__incorrectPromptBox svg { display: none; }
  `)
  return sheet
})()

/** A blank's typed value (an untouched blank reads as empty). */
const blankValue = (field: MathfieldElement, slot: string) =>
  field.getPromptValue(slot).replace(/\\placeholder\{\}/g, '').trim()

/**
 * The Help view: the answer's structure rendered as real math (stacked Σ bounds, raised
 * exponents, stacked fractions), with an empty box for every number and each group's label
 * underneath. Each group is a read-only MathLive field whose blanks are editable; wrong blanks
 * are marked after checking.
 */
export function HelpSkeleton({ skeleton, wrongSlots, onChange, onSubmit }: HelpSkeletonProps) {
  return (
    <div className="flex flex-wrap items-start gap-x-3 gap-y-4">
      {skeleton.parts.map((part, index) =>
        'op' in part ? (
          <Tex key={index} latex={part.op.latex} className="pt-3 text-2xl" />
        ) : (
          <SkeletonGroup
            key={index}
            label={part.group.label}
            latex={part.group.latex}
            autoFocus={index === 0}
            wrongSlots={wrongSlots}
            onChange={onChange}
            onSubmit={onSubmit}
          />
        ),
      )}
    </div>
  )
}

interface GroupProps {
  label: string
  latex: string
  autoFocus: boolean
  wrongSlots: string[]
  onChange: (slot: string, value: string) => void
  onSubmit: () => void
}

function SkeletonGroup({ label, latex, autoFocus, wrongSlots, onChange, onSubmit }: GroupProps) {
  const ref = useRef<MathfieldElement>(null)
  const callbacks = useRef({ onChange, onSubmit })
  useEffect(() => {
    callbacks.current = { onChange, onSubmit }
  })
  const slots = slotIds(latex)

  useEffect(() => {
    const field = ref.current
    if (!field) return
    field.readOnly = true
    if (wrongBlankStyle && field.shadowRoot && !field.shadowRoot.adoptedStyleSheets.includes(wrongBlankStyle)) {
      field.shadowRoot.adoptedStyleSheets = [...field.shadowRoot.adoptedStyleSheets, wrongBlankStyle]
    }
    field.mathVirtualKeyboardPolicy = 'auto'
    field.value = withBlanks(latex)
    if (autoFocus) field.focus()

    const handleInput = () => {
      for (const slot of slotIds(latex)) {
        callbacks.current.onChange(slot, blankValue(field, slot))
        field.setPromptState(slot, undefined)
      }
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Enter') {
        event.preventDefault()
        callbacks.current.onSubmit()
      }
    }
    field.addEventListener('input', handleInput)
    field.addEventListener('keydown', handleKeyDown, { capture: true })
    return () => {
      field.removeEventListener('input', handleInput)
      field.removeEventListener('keydown', handleKeyDown, { capture: true })
    }
  }, [latex, autoFocus])

  // Mark exactly the blanks that are wrong; the rest go back to normal.
  useEffect(() => {
    const field = ref.current
    if (!field) return
    for (const slot of slotIds(latex)) field.setPromptState(slot, wrongSlots.includes(slot) ? 'incorrect' : undefined)
  }, [latex, wrongSlots])

  const wrongHere = slots.filter((s) => wrongSlots.includes(s)).length
  return (
    <span role="group" aria-label={label} className="inline-flex flex-col items-center">
      <math-field
        ref={ref}
        aria-label={`${label}: fill in ${slots.length === 1 ? 'the blank' : `${slots.length} blanks`}`}
        className="skeleton-field rounded-lg bg-transparent px-1 text-2xl"
      />
      <span className="mt-1 text-sm text-ink-muted">
        {label}
        {wrongHere > 0 && <span className="sr-only">, {wrongHere} wrong</span>}
      </span>
    </span>
  )
}
