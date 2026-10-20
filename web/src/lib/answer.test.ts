import { describe, expect, it } from 'vitest'
import golden from '../data/golden/committee-mixed.json'
import type { Problem } from '../types/problem'
import { gradeFreeAnswer, gradeSkeleton, skeletonLatex } from './answer'

const problem = golden as Problem
const [defaultInstance, biggerInstance] = problem.instances
const slots = (a: string, b: string, c: string, d: string) => ({ a, b, c, d })

describe('gradeFreeAnswer', () => {
  it('accepts any equivalent expression', () => {
    expect(gradeFreeAnswer('\\binom{8}{3}\\binom{6}{2}', problem, defaultInstance)).toEqual({ kind: 'correct' })
    expect(gradeFreeAnswer('56\\times15', problem, defaultInstance)).toEqual({ kind: 'correct' })
    expect(gradeFreeAnswer('\\binom{10}{4}\\binom{7}{3}', problem, biggerInstance)).toEqual({ kind: 'correct' })
  })

  it('names recognised mistakes', () => {
    expect(gradeFreeAnswer('\\binom{8}{3}+\\binom{6}{2}', problem, defaultInstance)).toMatchObject({ kind: 'wrong', mistakeTag: 'add-vs-multiply' })
    expect(gradeFreeAnswer('\\binom{14}{5}', problem, defaultInstance)).toMatchObject({ kind: 'wrong', mistakeTag: 'overcount' })
    expect(gradeFreeAnswer('336\\times30', problem, defaultInstance)).toMatchObject({ kind: 'wrong', mistakeTag: 'order-confusion' })
  })

  it('gives plain feedback for an unrecognised mistake', () => {
    expect(gradeFreeAnswer('841', problem, defaultInstance)).toEqual({ kind: 'wrong' })
  })
})

describe('gradeSkeleton', () => {
  it('builds gradeable LaTeX from the slot values, each wrapped as a group', () => {
    expect(skeletonLatex(problem.answer.skeleton, slots('8', '3', '6', '2'))).toBe('\\binom{{8}}{{3}}\\times\\binom{{6}}{{2}}')
  })

  it('decides by value, so a swapped but equal binomial counts', () => {
    expect(gradeSkeleton(slots('8', '3', '6', '2'), problem, defaultInstance)).toEqual({ kind: 'correct', wrongSlots: [] })
    expect(gradeSkeleton(slots('8', '5', '6', '4'), problem, defaultInstance)).toEqual({ kind: 'correct', wrongSlots: [] })
  })

  it('flags only slots in groups that are actually wrong', () => {
    expect(gradeSkeleton(slots('8', '3', '6', '3'), problem, defaultInstance)).toEqual({ kind: 'wrong', wrongSlots: ['d'] })
    // C(8,5) equals C(8,3), so the 5 is fine; only the seniors' group is wrong.
    expect(gradeSkeleton(slots('8', '5', '6', '1'), problem, defaultInstance)).toEqual({ kind: 'wrong', wrongSlots: ['d'] })
    expect(gradeSkeleton(slots('8', '3', '6', '4'), problem, biggerInstance)).toMatchObject({ kind: 'wrong', wrongSlots: ['a', 'b', 'c', 'd'] })
  })

  it('names a recognised slot mistake', () => {
    expect(gradeSkeleton(slots('14', '3', '6', '2'), problem, defaultInstance)).toMatchObject({
      kind: 'wrong',
      mistakeTag: 'overcount',
      wrongSlots: ['a'],
    })
  })

  it('asks for every box before grading', () => {
    expect(gradeSkeleton(slots('8', '', '6', '2'), problem, defaultInstance)).toMatchObject({ kind: 'invalid' })
    expect(gradeSkeleton(slots('8', 'x', '6', '2'), problem, defaultInstance)).toMatchObject({ kind: 'invalid', wrongSlots: ['b'] })
  })
})
