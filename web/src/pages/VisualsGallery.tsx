import { OutcomeVisual } from '../components/OutcomeVisual'
import { outcomeText } from '../lib/outcome'
import type { InstanceExample, Outcome, VisualType } from '../types/problem'

/** Dev-only page (/dev/visuals): every diagram type with sample data, for design review. */

type Extra = Partial<Pick<InstanceExample, 'pool' | 'captions'>> & { highlight?: number[] }

const SAMPLES: { type: VisualType; title: string; yes: Outcome; extra?: Extra }[] = [
  { type: 'dice', title: 'Dice: 5 rolls, the 6s highlighted', yes: [6, 6, 1, 3, 2], extra: { highlight: [0, 1] } },
  { type: 'coins', title: 'Coins: 4 flips, heads highlighted', yes: ['H', 'T', 'H', 'T'], extra: { highlight: [0, 2] } },
  { type: 'sequence', title: 'Sequence: roles, with captions', yes: ['J1', 'T1'], extra: { captions: ['president', 'advisor'] } },
  { type: 'sequence', title: 'Sequence: a word arrangement', yes: ['B', 'A', 'N', 'A', 'N', 'A'], extra: { highlight: [1, 3, 5] } },
  { type: 'circle', title: 'Circle: 6 people at a round table', yes: ['A', 'B', 'C', 'D', 'E', 'F'], extra: { highlight: [0] } },
  { type: 'subset', title: 'Subset: 3 juniors + 2 seniors from 14', yes: ['J1', 'J2', 'J3', 'S1', 'S2'], extra: { pool: { juniors: Array.from({ length: 8 }, (_, i) => `J${i + 1}`), seniors: Array.from({ length: 6 }, (_, i) => `S${i + 1}`) } } },
  { type: 'boxes', title: 'Boxes: 5 balls in 3 boxes', yes: [2, 0, 3] },
  { type: 'stars-bars', title: 'Stars & bars: 7 cookies, 3 kids', yes: [3, 0, 4], extra: { captions: ['A', 'B', 'C'] } },
  { type: 'cards', title: 'Cards: a 5-card hand, hearts highlighted', yes: ['AH', 'KH', '7S', '7D', '2C'], extra: { highlight: [0, 1] } },
  { type: 'path', title: 'Path: 4 right, 3 up', yes: ['R', 'R', 'U', 'R', 'U', 'U', 'R'] },
  { type: 'matching', title: 'Matching: 4 letters into envelopes, none right', yes: [2, 1, 4, 3], extra: { highlight: [] } },
]

export function VisualsGallery() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <h1 className="text-xl font-bold">Diagram types (D4 · Pantry pieces)</h1>
      <p className="mt-1 text-ink-muted">Dev-only preview of every visual type, drawn by the real component.</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {SAMPLES.map(({ type, title, yes, extra }) => {
          const highlight = (extra?.highlight as number[] | undefined) ?? []
          const side = { outcome: yes, text: outcomeText(type, yes, extra?.captions), reason: '', highlight }
          const example = { side, pool: extra?.pool, captions: extra?.captions }
          return (
            <section key={title} className="rounded-xl border border-border bg-card p-4">
              <h2 className="mb-3 text-sm font-bold">{title}</h2>
              <OutcomeVisual type={type} {...example} />
              <p className="mt-3 text-center text-sm text-ink-muted">{side.text}</p>
            </section>
          )
        })}
      </div>
    </div>
  )
}
