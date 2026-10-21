import type { ReactNode } from 'react'
import { card } from '../lib/outcome'
import type { ExampleOutcome, InstanceExample, VisualType } from '../types/problem'

/*
 * The "one outcome" diagram (DESIGN.md, D4 · Pantry pieces): chunky pieces with an ink outline
 * and a small offset shadow; highlighted pieces are solid accent. Each visual type has a small
 * renderer that turns the outcome data into SVG. Colours come only from the theme tokens.
 */

const SHADOW = 3
const OUTLINE = 2.5

type Draw = { width: number; height: number; body: ReactNode }

interface PieceProps {
  x: number
  y: number
  w: number
  h: number
  hi?: boolean
  r?: number
}

function Tile({ x, y, w, h, hi = false, r = 9 }: PieceProps) {
  return (
    <>
      <rect x={x + SHADOW} y={y + SHADOW} width={w} height={h} rx={r} className="fill-border" />
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={r}
        strokeWidth={OUTLINE}
        className={`stroke-ink ${hi ? 'fill-accent' : 'fill-card'}`}
      />
    </>
  )
}

function Bead({ cx, cy, r, fill }: { cx: number; cy: number; r: number; fill: string }) {
  return (
    <>
      <circle cx={cx + SHADOW - 0.5} cy={cy + SHADOW - 0.5} r={r} className="fill-border" />
      <circle cx={cx} cy={cy} r={r} strokeWidth={OUTLINE} className={`stroke-ink ${fill}`} />
    </>
  )
}

function Label({ x, y, children, hi = false, size = 16 }: { x: number; y: number; children: ReactNode; hi?: boolean; size?: number }) {
  return (
    <text x={x} y={y} textAnchor="middle" dominantBaseline="central" fontSize={size} fontWeight={700} className={hi ? 'fill-on-accent' : 'fill-ink'}>
      {children}
    </text>
  )
}

function Caption({ x, y, children }: { x: number; y: number; children: ReactNode }) {
  return (
    <text x={x} y={y} textAnchor="middle" fontSize={12} className="fill-ink-muted">
      {children}
    </text>
  )
}

const PIPS: Record<number, [number, number][]> = {
  1: [[0.5, 0.5]],
  2: [[0.27, 0.27], [0.73, 0.73]],
  3: [[0.27, 0.27], [0.5, 0.5], [0.73, 0.73]],
  4: [[0.27, 0.27], [0.73, 0.27], [0.27, 0.73], [0.73, 0.73]],
  5: [[0.27, 0.27], [0.73, 0.27], [0.5, 0.5], [0.27, 0.73], [0.73, 0.73]],
  6: [[0.27, 0.25], [0.73, 0.25], [0.27, 0.5], [0.73, 0.5], [0.27, 0.75], [0.73, 0.75]],
}

/** Pieces laid out in a row, with a caption under each. */
function row(
  count: number,
  size: { w: number; h: number; gap: number },
  piece: (i: number, x: number, y: number) => ReactNode,
  caption: (i: number) => string | undefined,
): Draw {
  const step = size.w + size.gap
  const hasCaptions = Array.from({ length: count }, (_, i) => caption(i)).some(Boolean)
  return {
    width: count * step - size.gap + 2 * 4 + SHADOW,
    height: size.h + SHADOW + 8 + (hasCaptions ? 22 : 0),
    body: Array.from({ length: count }, (_, i) => {
      const x = 4 + i * step
      return (
        <g key={i}>
          {piece(i, x, 4)}
          {caption(i) && <Caption x={x + size.w / 2} y={size.h + 26}>{caption(i)}</Caption>}
        </g>
      )
    }),
  }
}

/** What a diagram needs: one outcome, plus the instance's pool and captions. */
type DrawInput = { side: ExampleOutcome; pool?: InstanceExample['pool']; captions?: string[] }

function draw(type: VisualType, example: DrawInput): Draw {
  const { outcome } = example.side
  const hi = (i: number) => example.side.highlight.includes(i)
  const caption = (fallback: (i: number) => string | undefined) => (i: number) => example.captions?.[i] ?? fallback(i)

  switch (type) {
    case 'dice':
      return row(outcome.length, { w: 48, h: 48, gap: 12 }, (i, x, y) => (
        <>
          <Tile x={x} y={y} w={48} h={48} hi={hi(i)} />
          {(PIPS[Number(outcome[i])] ?? []).map(([px, py], k) => (
            <circle key={k} cx={x + px * 48} cy={y + py * 48} r={4.2} className={hi(i) ? 'fill-on-accent' : 'fill-ink'} />
          ))}
        </>
      ), caption((i) => `roll ${i + 1}`))

    case 'coins':
      return row(outcome.length, { w: 44, h: 44, gap: 10 }, (i, x, y) => (
        <>
          <Bead cx={x + 22} cy={y + 22} r={21} fill={hi(i) ? 'fill-accent' : 'fill-card'} />
          <Label x={x + 22} y={y + 22} hi={hi(i)} size={18}>{outcome[i]}</Label>
        </>
      ), caption((i) => `flip ${i + 1}`))

    case 'sequence':
      return row(outcome.length, { w: 50, h: 44, gap: 10 }, (i, x, y) => (
        <>
          <Tile x={x} y={y} w={50} h={44} hi={hi(i)} />
          <Label x={x + 25} y={y + 22} hi={hi(i)}>{outcome[i]}</Label>
        </>
      ), caption(() => undefined))

    case 'circle': {
      const n = outcome.length
      const R = n <= 6 ? 56 : 70
      const c = R + 24
      return {
        width: 2 * c + SHADOW,
        height: 2 * c + SHADOW,
        body: (
          <>
            <circle cx={c} cy={c} r={R} fill="none" strokeWidth={2} className="stroke-border" />
            <text x={c} y={c} textAnchor="middle" dominantBaseline="central" fontSize={22} className="fill-ink-muted">↻</text>
            {outcome.map((label, i) => {
              const a = -Math.PI / 2 + (i * 2 * Math.PI) / n
              const x = c + R * Math.cos(a)
              const y = c + R * Math.sin(a)
              return (
                <g key={i}>
                  <Bead cx={x} cy={y} r={17} fill={hi(i) ? 'fill-accent' : 'fill-card'} />
                  <Label x={x} y={y} hi={hi(i)} size={14}>{label}</Label>
                </g>
              )
            })}
          </>
        ),
      }
    }

    case 'subset': {
      // Each named group (e.g. juniors, seniors) gets its own labelled row, so different kinds
      // of people don't look interchangeable.
      const pool = example.pool ?? outcome.map(String)
      const groups = Array.isArray(pool) ? [['', pool] as const] : Object.entries(pool)
      const chosen = new Set(outcome.map(String))
      const perRow = Math.min(Math.max(...groups.map(([, items]) => items.length)), 10)
      const named = groups.some(([name]) => name)
      const left = 4
      let y = 4
      const body: ReactNode[] = []
      groups.forEach(([name, items], g) => {
        if (g > 0) y += 10
        if (named) {
          body.push(<text key={`name${g}`} x={left} y={y + 12} fontSize={13} fontWeight={700} className="fill-ink-muted">{name}</text>)
          y += 20
        }
        items.forEach((label, i) => {
          const x = left + (i % perRow) * 46
          const top = y + Math.floor(i / perRow) * 46
          const on = chosen.has(label)
          body.push(
            <g key={label} opacity={on ? 1 : 0.55}>
              <Tile x={x} y={top} w={38} h={38} hi={on} r={8} />
              <Label x={x + 19} y={top + 19} hi={on} size={13}>{label}</Label>
            </g>,
          )
        })
        y += Math.ceil(items.length / perRow) * 46
      })
      return { width: perRow * 46 + left + SHADOW, height: y + SHADOW, body }
    }

    case 'boxes':
      return row(outcome.length, { w: 76, h: 62, gap: 12 }, (i, x, y) => {
        const balls = Number(outcome[i])
        return (
          <>
            <path d={`M${x + SHADOW} ${y + SHADOW} v58 h72 v-58`} fill="none" strokeWidth={OUTLINE} className="stroke-border" />
            <path d={`M${x} ${y} v58 h72 v-58`} fill="none" strokeWidth={OUTLINE + 0.5} strokeLinejoin="round" className="stroke-ink" />
            {Array.from({ length: balls }, (_, k) => (
              <Bead key={k} cx={x + 14 + (k % 4) * 15} cy={y + 46 - Math.floor(k / 4) * 15} r={6.5} fill={hi(i) ? 'fill-deco' : 'fill-accent'} />
            ))}
          </>
        )
      }, caption((i) => `box ${i + 1}: ${outcome[i]}`))

    case 'stars-bars': {
      // Stars for items, bars as dividers; with captions, each group's name sits under it.
      const body: ReactNode[] = []
      let x = 6
      outcome.forEach((v, i) => {
        if (i > 0) {
          body.push(<rect key={`bar${i}`} x={x + 4} y={8} width={7} height={44} rx={2} strokeWidth={2} className="fill-deco stroke-ink" />)
          x += 20
        }
        const start = x
        for (let k = 0; k < Number(v); k++) {
          body.push(<Bead key={`s${i}-${k}`} cx={x + 12} cy={30} r={11} fill={hi(i) ? 'fill-deco' : 'fill-accent'} />)
          x += 30
        }
        if (Number(v) === 0) x += 14
        const label = example.captions?.[i]
        if (label) body.push(<Caption key={`c${i}`} x={(start + x) / 2} y={74}>{label}</Caption>)
      })
      return { width: x + 6, height: example.captions ? 82 : 60, body }
    }

    case 'cards':
      return row(outcome.length, { w: 44, h: 62, gap: 8 }, (i, x, y) => {
        const c = card(String(outcome[i]))
        const color = hi(i) ? 'fill-on-accent' : c.red ? 'fill-wrong-ink' : 'fill-ink'
        return (
          <>
            <Tile x={x} y={y} w={44} h={62} hi={hi(i)} r={6} />
            <text x={x + 22} y={y + 24} textAnchor="middle" fontSize={16} fontWeight={700} className={color}>{c.rank}</text>
            <text x={x + 22} y={y + 47} textAnchor="middle" fontSize={18} className={color}>{c.suit}</text>
          </>
        )
      }, caption(() => undefined))

    case 'path': {
      const cols = outcome.filter((s) => s === 'R').length
      const rowsN = outcome.length - cols
      const cell = 34
      const pad = 14
      const h = rowsN * cell
      const pts: [number, number][] = [[0, 0]]
      outcome.forEach((s) => {
        const [px, py] = pts[pts.length - 1]
        pts.push(s === 'R' ? [px + 1, py] : [px, py + 1])
      })
      const sx = (gx: number) => pad + gx * cell
      const sy = (gy: number) => pad + h - gy * cell
      return {
        width: cols * cell + 2 * pad,
        height: h + 2 * pad,
        body: (
          <>
            {Array.from({ length: cols + 1 }, (_, i) => (
              <line key={`v${i}`} x1={sx(i)} y1={sy(0)} x2={sx(i)} y2={sy(rowsN)} strokeWidth={1.5} className="stroke-border" />
            ))}
            {Array.from({ length: rowsN + 1 }, (_, j) => (
              <line key={`h${j}`} x1={sx(0)} y1={sy(j)} x2={sx(cols)} y2={sy(j)} strokeWidth={1.5} className="stroke-border" />
            ))}
            <polyline points={pts.map(([gx, gy]) => `${sx(gx)},${sy(gy)}`).join(' ')} fill="none" strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" className="stroke-accent" />
            {pts.map(([gx, gy], i) => (
              <Bead key={i} cx={sx(gx)} cy={sy(gy)} r={i === 0 || i === pts.length - 1 ? 7 : 4.5} fill={i === 0 || i === pts.length - 1 ? 'fill-deco' : 'fill-card'} />
            ))}
          </>
        ),
      }
    }

    case 'matching': {
      // Items on top, spots below (e.g. people and hats); captions label the two rows.
      const n = outcome.length
      const step = 50
      const left = example.captions ? 64 : 8
      const top = 6
      const bottom = 96
      const cx = (i: number) => left + i * step + 19
      return {
        width: left + n * step + SHADOW,
        height: bottom + 38 + SHADOW + 4,
        body: (
          <>
            {example.captions && (
              <>
                <text x={0} y={top + 24} fontSize={13} fontWeight={700} className="fill-ink-muted">{example.captions[0]}</text>
                <text x={0} y={bottom + 24} fontSize={13} fontWeight={700} className="fill-ink-muted">{example.captions[1]}</text>
              </>
            )}
            {outcome.map((spot, i) => (
              <line key={`l${i}`} x1={cx(i)} y1={top + 40} x2={cx(Number(spot) - 1)} y2={bottom} strokeWidth={hi(i) ? 4 : 2.5} className={hi(i) ? 'stroke-accent' : 'stroke-ink-muted'} />
            ))}
            {outcome.map((_, i) => (
              <g key={i}>
                <Bead cx={cx(i)} cy={top + 19} r={18} fill={hi(i) ? 'fill-accent' : 'fill-card'} />
                <Label x={cx(i)} y={top + 19} hi={hi(i)} size={14}>{i + 1}</Label>
                <Tile x={cx(i) - 19} y={bottom} w={38} h={38} r={6} />
                <Label x={cx(i)} y={bottom + 19} size={14}>{i + 1}</Label>
              </g>
            ))}
          </>
        ),
      }
    }
  }
}

/** A small diagram of one outcome. Its text form is the accessible name. */
export function OutcomeVisual({ type, side, pool, captions }: { type: VisualType } & DrawInput) {
  const { width, height, body } = draw(type, { side, pool, captions })
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      className="mx-auto block h-auto max-w-full"
      role="img"
      aria-label={`One outcome: ${side.text}`}
    >
      {body}
    </svg>
  )
}
