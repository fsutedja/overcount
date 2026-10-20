import logoMark from '../assets/logo-mark.svg'
import { ThemeToggle } from './ThemeToggle'

const NAV_ITEMS = ['Roadmap', 'Practice', 'Progress'] as const

export function Header() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-5xl items-center gap-5 px-4 py-3">
        <a href="/" className="flex items-center gap-1.5" aria-label="Overcount home">
          <img src={logoMark} alt="" className="h-7 w-auto [image-rendering:pixelated]" />
          <span className="font-pixel text-2xl leading-none">
            <span className="text-accent-ink">over</span>
            <span className="text-deco">count</span>
          </span>
        </a>
        <nav aria-label="Main" className="hidden gap-4 text-sm font-bold text-ink-muted sm:flex">
          {NAV_ITEMS.map((item) => (
            <span key={item} title="Coming soon">
              {item}
            </span>
          ))}
        </nav>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
