/** Shown before dots are hidden behind a "+n" count, so long histories stay one short line. */
const MAX_DOTS = 8

/**
 * One mark per try (DESIGN.md, D5 and D10): a filled green dot for right, a hollow berry ring for
 * wrong, so they differ by shape as well as colour. A first-try right answer is a single green
 * dot. With `next`, a dashed circle marks the try about to be made.
 */
export function TryDots({ tries, next = false }: { tries: boolean[]; next?: boolean }) {
  if (!tries.length && !next) return null
  const hidden = Math.max(0, tries.length - MAX_DOTS)
  const shown = tries.slice(hidden)
  const right = tries.filter(Boolean).length
  const label = `${tries.length} ${tries.length === 1 ? 'try' : 'tries'}, ${right ? 'solved' : 'not solved yet'}`
  return (
    <span className="inline-flex items-center gap-[3px] align-middle" role="img" aria-label={label}>
      {hidden > 0 && <span className="mr-1 text-xs text-ink-muted">+{hidden}</span>}
      {shown.map((ok, i) => (
        <span key={i} className={`size-2.5 rounded-full ${ok ? 'bg-correct-ink' : 'border-2 border-wrong-ink'}`} />
      ))}
      {next && <span className="size-2.5 rounded-full border-2 border-dashed border-ink-muted/60" />}
    </span>
  )
}
