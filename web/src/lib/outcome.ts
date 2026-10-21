import type { Outcome, VisualType } from '../types/problem'

// Mirrors outcome_text in pipeline/src/overcount/visual.py. The bank test checks that every
// published text equals what this function produces, so the two can't drift apart.

const SUITS: Record<string, string> = { H: '♥', D: '♦', C: '♣', S: '♠' }

export const card = (code: string) => ({ rank: code.slice(0, -1), suit: SUITS[code.slice(-1)] ?? '?', red: /[HD]$/.test(code) })

/** The outcome written out for reading, e.g. "6, 6, 1, 3, 2" or "★★ | ★ | ★★★". */
export function outcomeText(type: VisualType, outcome: Outcome): string {
  const items = outcome.map(String)
  switch (type) {
    case 'circle':
      return `${items.join(' → ')} → (back to ${items[0]})`
    case 'subset':
      return `{${items.join(', ')}}`
    case 'boxes':
      return items.join(' | ')
    case 'stars-bars':
      return outcome.map((v) => (Number(v) ? '★'.repeat(Number(v)) : '–')).join(' | ')
    case 'cards':
      return items.map((c) => card(c).rank + card(c).suit).join(' ')
    case 'path':
      return items.join(' ')
    case 'matching':
      return items.map((spot, i) => `${i + 1}→${spot}`).join(', ')
    default:
      return items.join(', ')
  }
}
