import type { DeckGroup } from '../types/problem'

const RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
const SUITS: [string, string, boolean][] = [
  ['H', '♥', true],
  ['D', '♦', true],
  ['C', '♣', false],
  ['S', '♠', false],
]
const STRIPES = 'repeating-linear-gradient(135deg, var(--accent-soft) 0 4px, var(--deco-soft) 4px 8px)'

const inGroup = (group: DeckGroup, rank: string, suit: string) =>
  (!group.suits?.length || group.suits.includes(suit)) && (!group.ranks?.length || group.ranks.includes(rank))

/**
 * The 13×4 card-deck grid (DESIGN.md, D11): suits as rows, ranks as columns. The first group is
 * shaded teal, the second terracotta, cards in both are striped, and the hand's cards get a
 * thick ink outline (the hand that counts). The legend names each group with its size.
 */
export function DeckGrid({ groups, hand }: { groups: DeckGroup[]; hand: string[] }) {
  const [first, second] = groups
  const all = SUITS.flatMap(([suit]) => RANKS.map((rank) => ({ rank, suit })))
  const count = (test: (rank: string, suit: string) => boolean) => all.filter(({ rank, suit }) => test(rank, suit)).length
  const background = (rank: string, suit: string) => {
    const a = first && inGroup(first, rank, suit)
    const b = second && inGroup(second, rank, suit)
    return a && b ? STRIPES : a ? 'var(--accent-soft)' : b ? 'var(--deco-soft)' : undefined
  }

  return (
    <figure className="m-0 mb-2">
      <div
        className="mx-auto grid max-w-[34rem] items-center gap-[3px]"
        style={{ gridTemplateColumns: '1.5rem repeat(13, minmax(0, 1fr))' }}
        role="img"
        aria-label={`A deck of 52 cards with the hand ${hand.join(', ')} outlined${groups.length ? `; shaded: ${groups.map((g) => g.label).join(' and ')}` : ''}`}
      >
        <span />
        {RANKS.map((rank) => (
          <span key={rank} className="text-center text-[11px] font-bold text-ink-muted">
            {rank}
          </span>
        ))}
        {SUITS.map(([suit, symbol, red]) => (
          <div key={suit} className="contents">
            <span className={`text-center ${red ? 'text-wrong-ink' : 'text-ink'}`}>{symbol}</span>
            {RANKS.map((rank) => {
              const held = hand.includes(rank + suit)
              return (
                <span
                  key={rank}
                  className={`grid aspect-[3/4] place-items-center rounded-[4px] text-[11px] font-bold ${
                    held ? 'border-[2.5px] border-ink' : 'border border-border'
                  } ${red ? 'text-wrong-ink' : held ? 'text-ink' : 'text-ink-muted'}`}
                  style={{ background: background(rank, suit) ?? 'var(--card)' }}
                >
                  {rank}
                </span>
              )
            })}
          </div>
        ))}
      </div>
      <figcaption className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-ink-muted">
        {first && (
          <span className="flex items-center gap-1.5">
            <span className="h-4 w-3 rounded-[3px] border border-border bg-accent-soft" />
            {first.label} ({count((r, s) => inGroup(first, r, s))})
          </span>
        )}
        {second && (
          <span className="flex items-center gap-1.5">
            <span className="h-4 w-3 rounded-[3px] border border-border bg-deco-soft" />
            {second.label} ({count((r, s) => inGroup(second, r, s))})
          </span>
        )}
        {first && second && (
          <span className="flex items-center gap-1.5">
            <span className="h-4 w-3 rounded-[3px] border border-border" style={{ background: STRIPES }} />
            both ({count((r, s) => inGroup(first, r, s) && inGroup(second, r, s))})
          </span>
        )}
        <span className="flex items-center gap-1.5">
          <span className="h-4 w-3 rounded-[3px] border-[2.5px] border-ink" />
          the hand that counts
        </span>
      </figcaption>
    </figure>
  )
}
