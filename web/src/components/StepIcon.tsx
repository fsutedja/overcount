import type { StepKind } from '../types/problem'

/** Math-symbol icon per step kind (DESIGN.md, D2). Never hints at a blank's answer. */
const SYMBOLS: Record<StepKind, string> = {
  choose: 'C',
  arrange: 'P',
  combine: '×+',
  cases: 'Σ',
  'inclusion-exclusion': '∪',
  complement: '1−',
  overcount: '÷',
  condition: 'A|B',
  distribution: '∼',
}

export function StepIcon({ kind }: { kind: StepKind }) {
  const symbol = SYMBOLS[kind]
  return (
    <span
      aria-hidden="true"
      className={`inline-flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent-soft font-bold leading-none text-accent-ink ${
        symbol.length > 2 ? 'text-xs' : symbol.length === 2 ? 'text-sm' : 'text-base'
      }`}
    >
      {symbol}
    </span>
  )
}
