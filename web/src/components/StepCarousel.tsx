import { useState, type ReactNode } from 'react'

/**
 * One slide at a time with round ‹ › arrow buttons (DESIGN.md, Help flow); ← and → keys work
 * too. Used for Help's why-steps and for the worked solution.
 */
export function StepCarousel({ label, slides, captions }: { label: string; slides: ReactNode[]; captions: string[] }) {
  const [index, setIndex] = useState(0)
  const go = (next: number) => setIndex(Math.min(slides.length - 1, Math.max(0, next)))

  return (
    <div
      role="group"
      aria-roledescription="carousel"
      aria-label={label}
      onKeyDown={(event) => {
        if (event.key === 'ArrowRight') go(index + 1)
        if (event.key === 'ArrowLeft') go(index - 1)
      }}
    >
      <div className="flex items-stretch gap-2">
        <Arrow direction="previous" disabled={index === 0} onClick={() => go(index - 1)} />
        <div className="min-w-0 flex-1" aria-live="polite">
          {slides[index]}
        </div>
        <Arrow direction="next" disabled={index === slides.length - 1} onClick={() => go(index + 1)} />
      </div>
      <p className="mt-2 text-center text-sm text-ink-muted">{captions[index]}</p>
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
