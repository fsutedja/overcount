import type { Difficulty as Level } from '../types/problem'

const STYLE: Record<Level, { chip: string; text: string; bars: number; label: string }> = {
  easy: { chip: 'bg-correct-bg text-correct-ink', text: 'text-correct-ink', bars: 1, label: 'Easy' },
  medium: { chip: 'bg-amber-bg text-amber-ink', text: 'text-amber-ink', bars: 2, label: 'Medium' },
  hard: { chip: 'bg-wrong-bg text-wrong-ink', text: 'text-wrong-ink', bars: 3, label: 'Hard' },
}

/**
 * 1, 2 or 3 signal bars, so difficulty never relies on colour alone. Heights are in em so the
 * tallest matches the capitals at any text size; the parent aligns them to the text baseline.
 */
function Bars({ count }: { count: number }) {
  return (
    <span className="inline-flex items-end gap-[2px]" aria-hidden="true">
      {['0.3em', '0.5em', '0.7em'].map((height, i) => (
        <span key={height} className={`w-[3px] rounded-[1px] bg-current ${i < count ? '' : 'opacity-25'}`} style={{ height }} />
      ))}
    </span>
  )
}

/**
 * Difficulty, colour-coded (DESIGN.md, D13): green easy, amber medium, red hard, each with
 * signal bars. `chip` is the tinted label for lists; `text` is just the coloured word.
 */
export function Difficulty({ level, variant = 'chip' }: { level: Level; variant?: 'chip' | 'text' }) {
  const { chip, text, bars, label } = STYLE[level]
  return (
    <span
      className={`inline-flex items-baseline gap-1.5 font-bold ${variant === 'chip' ? `rounded-md px-2 py-0.5 ${chip}` : text}`}
    >
      <Bars count={bars} />
      {label}
    </span>
  )
}
