import { describe, expect, it } from 'vitest'
import { formatValue, gradeLatex, matchesLatex } from './grade'
import type { StoredValue } from '../types/problem'

const rational = (exact: string): StoredValue => ({ type: 'rational', exact })

describe('gradeLatex', () => {
  it('accepts any expression equal to the answer', () => {
    const teams = rational('840')
    expect(gradeLatex('\\binom{8}{3}\\cdot\\binom{6}{2}', teams)).toEqual({ kind: 'correct' })
    expect(gradeLatex('\\binom{8}{5}\\binom{6}{4}', teams)).toEqual({ kind: 'correct' })
    expect(gradeLatex('\\frac{\\operatorname{P}(8,3)}{3!}\\times 15', teams)).toEqual({ kind: 'correct' })
    expect(gradeLatex('840', teams)).toEqual({ kind: 'correct' })
  })

  it('rejects a wrong value, such as ordered picks instead of unordered', () => {
    expect(gradeLatex('\\operatorname{P}(8,3)\\cdot\\binom{6}{2}', rational('840'))).toEqual({ kind: 'wrong' })
  })

  it('compares fractions exactly', () => {
    const fullHouse = rational('6/4165')
    const latex = '\\frac{\\binom{13}{1}\\binom{4}{3}\\binom{12}{1}\\binom{4}{2}}{\\binom{52}{5}}'
    expect(gradeLatex(latex, fullHouse)).toEqual({ kind: 'correct' })
    expect(gradeLatex('\\frac{14}{60}', rational('7/30'))).toEqual({ kind: 'correct' })
    expect(gradeLatex('0.2333333333', rational('7/30'))).toEqual({ kind: 'wrong' })
    expect(gradeLatex('0.5', rational('1/2'))).toEqual({ kind: 'correct' })
  })

  it('compares answers involving e within a tolerance', () => {
    const poisson: StoredValue = { type: 'real', approx: 0.18044704431548358 }
    expect(gradeLatex('e^{-2}\\cdot\\frac{2^3}{3!}', poisson)).toEqual({ kind: 'correct' })
    expect(gradeLatex('e^{-2}\\cdot\\frac{2^2}{2!}', poisson)).toEqual({ kind: 'wrong' })
  })

  it('explains input it cannot grade instead of marking it wrong', () => {
    const teams = rational('840')
    expect(gradeLatex('', teams)).toMatchObject({ kind: 'invalid', message: 'Enter an answer first.' })
    expect(gradeLatex('\\binom{8}{}', teams)).toMatchObject({ kind: 'invalid' })
    expect(gradeLatex('x+1', teams)).toMatchObject({ kind: 'invalid', message: 'Use numbers only, no letters like x.' })
    expect(gradeLatex('\\frac{1}{0}', teams)).toMatchObject({ kind: 'invalid' })
    expect(gradeLatex('\\binom{2.5}{1}', teams)).toMatchObject({ kind: 'invalid' })
    expect(gradeLatex('100000!', teams)).toMatchObject({ kind: 'invalid' })
    expect(gradeLatex('2^{5000}', teams)).toMatchObject({ kind: 'invalid' })
  })
})

describe('matchesLatex', () => {
  it('recognises a known mistake by value, in any equivalent form', () => {
    const orderedPicks = '\\operatorname{P}\\left(8,3\\right)'
    expect(matchesLatex('\\operatorname{P}(8,3)', orderedPicks)).toBe(true)
    expect(matchesLatex('8\\cdot7\\cdot6', orderedPicks)).toBe(true)
    expect(matchesLatex('\\binom{8}{3}', orderedPicks)).toBe(false)
  })

  it('never matches input that cannot be graded', () => {
    expect(matchesLatex('', '0')).toBe(false)
    expect(matchesLatex('x', '0')).toBe(false)
  })
})

describe('formatValue', () => {
  it('adds thousands separators and keeps fractions exact', () => {
    expect(formatValue(rational('2598960'))).toBe('2,598,960')
    expect(formatValue(rational('6/4165'))).toBe('6/4,165')
    expect(formatValue({ type: 'real', approx: 0.18044704431548358 })).toBe('0.180447')
  })
})

describe('Σ answers', () => {
  const noMatch = rational('3/8')
  const pitman = '\\sum_{k=0}^{4}\\frac{(-1)^k}{k!}'

  it('grades sums exactly, in any equivalent form', () => {
    expect(gradeLatex(pitman, noMatch)).toEqual({ kind: 'correct' })
    expect(gradeLatex('\\frac{9}{24}', noMatch)).toEqual({ kind: 'correct' })
    expect(gradeLatex(`4!${pitman}`, rational('9'))).toEqual({ kind: 'correct' })
    expect(gradeLatex('\\sum_{k=0}^{3}\\frac{(-1)^k}{k!}', noMatch)).toEqual({ kind: 'wrong' })
  })

  it('allows the index letter only inside its own sum', () => {
    expect(gradeLatex('\\sum_{k=0}^{4}\\binom{4}{k}', rational('16'))).toEqual({ kind: 'correct' })
    expect(gradeLatex('k+\\sum_{k=0}^{4}k', rational('10'))).toMatchObject({ kind: 'invalid' })
    expect(gradeLatex('\\sum_{k=0}^{4}j', rational('0'))).toMatchObject({ kind: 'invalid' })
  })

  it('rejects sums with letters or huge ranges in the limits', () => {
    expect(gradeLatex('\\sum_{k=0}^{n}k', rational('0'))).toMatchObject({ kind: 'invalid' })
    expect(gradeLatex('\\sum_{k=0}^{5000}k', rational('0'))).toMatchObject({ kind: 'invalid' })
  })
})

describe('blanks inside a Σ that hold an expression in the index', () => {
  const expected = { type: 'indexed', latex: '6 - k', index: 'k' } as const

  it('accepts any equivalent form', () => {
    for (const latex of ['6-k', '-k+6', '\\frac{12-2k}{2}']) expect(gradeLatex(latex, expected)).toEqual({ kind: 'correct' })
  })

  it('rejects a different expression', () => {
    expect(gradeLatex('k-6', expected)).toEqual({ kind: 'wrong' })
    expect(gradeLatex('6', expected)).toEqual({ kind: 'wrong' })
  })

  it('rejects letters other than the index', () => {
    expect(gradeLatex('n-k', expected).kind).toBe('invalid')
  })

  it('grades a typed derangement in the unsimplified form', () => {
    const latex = '\\sum_{k=0}^{6}(-1)^{k}\\binom{6}{k}(6-k)!'
    expect(gradeLatex(latex, { type: 'rational', exact: '265' })).toEqual({ kind: 'correct' })
  })
})
