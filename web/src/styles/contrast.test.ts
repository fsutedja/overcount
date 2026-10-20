import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

/** WCAG 2.x contrast checks for every text/background pairing the UI uses, in both themes. */

const css = readFileSync(new URL('./tokens.css', import.meta.url), 'utf8')

function tokensFor(selector: string): Record<string, string> {
  const block = css.split(selector + ' {')[1]?.split('}')[0] ?? ''
  return Object.fromEntries([...block.matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)].map(([, name, hex]) => [name, hex]))
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  const linear = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

const BODY_TEXT = 4.5
const LARGE_TEXT_OR_UI = 3

const PAIRS: [foreground: string, background: string, minimum: number][] = [
  ['ink', 'bg', BODY_TEXT],
  ['ink', 'card', BODY_TEXT],
  ['ink', 'card-sunken', BODY_TEXT],
  ['ink-muted', 'bg', BODY_TEXT],
  ['ink-muted', 'card', BODY_TEXT],
  ['accent-ink', 'card', BODY_TEXT],
  ['accent-ink', 'accent-soft', BODY_TEXT],
  ['on-accent', 'accent-ink', BODY_TEXT],
  ['correct-ink', 'correct-bg', BODY_TEXT],
  ['wrong-ink', 'wrong-bg', BODY_TEXT],
  ['wrong-ink', 'card', LARGE_TEXT_OR_UI],
  ['accent', 'card', LARGE_TEXT_OR_UI],
  ['deco', 'card', LARGE_TEXT_OR_UI],
]

describe.each([
  ['light', ':root'],
  ['dark', ":root[data-theme='dark']"],
])('%s theme', (_, selector) => {
  const tokens = tokensFor(selector)

  it.each(PAIRS)('%s on %s meets %d:1', (foreground, background, minimum) => {
    expect(tokens[foreground], `missing token --${foreground}`).toBeDefined()
    expect(tokens[background], `missing token --${background}`).toBeDefined()
    expect(contrast(tokens[foreground], tokens[background])).toBeGreaterThanOrEqual(minimum)
  })
})
