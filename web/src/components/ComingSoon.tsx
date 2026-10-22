/**
 * The dashed "Coming soon" tag for methods and roadmap stops with no problems yet (DESIGN.md,
 * D17). Rows aren't faded, so their text stays readable; the dashed outline says "not ready".
 */
export function ComingSoon() {
  return (
    <span className="shrink-0 rounded-md border border-dashed border-ink-muted px-1.5 text-xs whitespace-nowrap text-ink-muted">
      Coming soon
    </span>
  )
}
