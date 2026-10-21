import { Link, NavLink } from 'react-router-dom'
import logoMark from '../assets/logo-mark.svg'
import { ThemeToggle } from './ThemeToggle'

/** Nav items without a page yet stay as plain, non-clickable labels. */
const NAV_ITEMS: { label: string; to?: string }[] = [
  { label: 'Roadmap', to: '/' },
  { label: 'Practice', to: '/practice' },
  { label: 'Progress' },
]

export function Header() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-5xl items-center gap-10 px-4 py-3">
        <Link to="/" className="flex items-center gap-3" aria-label="Overcount home">
          <img src={logoMark} alt="" className="h-7 w-auto [image-rendering:pixelated]" />
          <span className="font-pixel text-2xl leading-none">
            <span className="text-accent-ink">over</span>
            <span className="text-deco">count</span>
          </span>
        </Link>
        <nav aria-label="Main" className="hidden gap-7 text-sm font-bold text-ink-muted sm:flex">
          {NAV_ITEMS.map(({ label, to }) =>
            to ? (
              <NavLink
                key={label}
                to={to}
                end
                className={({ isActive }) =>
                  isActive
                    ? 'text-ink underline decoration-accent-ink decoration-2 underline-offset-4'
                    : 'hover:text-ink'
                }
              >
                {label}
              </NavLink>
            ) : (
              <span key={label} title="Coming soon">
                {label}
              </span>
            ),
          )}
        </nav>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
