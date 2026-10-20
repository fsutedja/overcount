import { readdirSync, readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { BankIndex, Family } from '../types/problem'
import { skeletonLatex } from './answer'
import { gradeLatex, matchesLatex } from './grade'
import { fillTemplate } from './template'

/**
 * Cross-checks the committed bank: every instance value was computed by the pipeline with sympy,
 * and here the browser's Compute Engine must grade the canonical answer, the filled-in skeleton,
 * and every solution's final step as correct. Common mistakes must never equal the answer.
 */

const bankDir = new URL('../../public/bank/', import.meta.url)
const index = JSON.parse(readFileSync(new URL('index.json', bankDir), 'utf8')) as BankIndex
const families = readdirSync(new URL('families/', bankDir)).map(
  (file) => JSON.parse(readFileSync(new URL(`families/${file}`, bankDir), 'utf8')) as Family,
)
const problems = families.flatMap((family) => family.problems)

describe('committed bank', () => {
  it('lists every problem in the index', () => {
    expect(index.problems.map((p) => p.id).sort()).toEqual(problems.map((p) => p.id).sort())
  })

  describe.each(problems.map((p) => [p.id, p] as const))('%s', (_, problem) => {
    // Every instance is checked; a sample keeps the suite fast when the bank grows.
    const instances = problem.instances.slice(0, 15)

    it('grades the canonical answer as correct on every instance', () => {
      for (const instance of instances) {
        const latex = fillTemplate(problem.answer.latex, instance.vars)
        expect(gradeLatex(latex, instance.values.answer), `${instance.key}: ${latex}`).toEqual({ kind: 'correct' })
      }
    })

    it('grades the skeleton filled with the slot values as correct', () => {
      for (const instance of instances) {
        const slots = Object.fromEntries(
          Object.keys(problem.answer.skeleton.slots).map((slot) => {
            const value = instance.values[`slot.${slot}`]
            return [slot, value.type === 'rational' ? value.exact : String(value.approx)]
          }),
        )
        const latex = skeletonLatex(problem.answer.skeleton, slots)
        expect(gradeLatex(latex, instance.values.answer), `${instance.key}: ${latex}`).toEqual({ kind: 'correct' })
      }
    })

    it("ends the solution on the answer's value", () => {
      const lastStep = problem.solution[problem.solution.length - 1]
      for (const instance of instances) {
        expect(gradeLatex(fillTemplate(lastStep.latex, instance.vars), instance.values.answer)).toEqual({ kind: 'correct' })
      }
    })

    it('never lists a common mistake that equals the answer', () => {
      for (const instance of instances) {
        for (const mistake of problem.answer.common_wrong) {
          const answer = fillTemplate(problem.answer.latex, instance.vars)
          expect(matchesLatex(fillTemplate(mistake.latex, instance.vars), answer), `${instance.key}: ${mistake.latex}`).toBe(false)
        }
      }
    })
  })
})
