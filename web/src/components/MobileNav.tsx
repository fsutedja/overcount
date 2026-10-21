import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

/** Small line icons, drawn in the link's text colour. */
const icon = (paths: ReactNode) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
    {paths}
  </svg>
)

const ITEMS = [
  {
    label: 'Roadmap',
    to: '/',
    icon: icon(
      <>
        <circle cx="4" cy="16" r="2.5" />
        <circle cx="16" cy="4" r="2.5" />
        <path d="M6 14 14 6" />
      </>,
    ),
  },
  {
    label: 'Practice',
    to: '/practice',
    icon: icon(
      <>
        <rect x="3" y="3" width="14" height="14" rx="2" />
        <path d="M7 8h6M7 12h4" />
      </>,
    ),
  },
  { label: 'Progress', to: '/progress', icon: icon(<path d="M3 17v-7M8 17V6M13 17v-5M18 17V3" />) },
]

/**
 * The phone tab bar (DESIGN.md, D15 · C): fixed at the bottom below 640px, where the header
 * links are hidden. `main` gets matching bottom padding so nothing sits under it.
 */
export function MobileNav() {
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-card pb-[env(safe-area-inset-bottom)] sm:hidden"
    >
      {ITEMS.map(({ label, to, icon }) => (
        <NavLink
          key={label}
          to={to}
          end
          className={({ isActive }) =>
            `flex flex-1 flex-col items-center gap-0.5 pt-2 pb-2.5 text-xs font-bold ${
              isActive ? 'text-accent-ink shadow-[inset_0_2px_0_var(--accent-ink)]' : 'text-ink-muted'
            }`
          }
        >
          {icon}
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
