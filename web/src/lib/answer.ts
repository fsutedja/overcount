import type { CommonWrong, Instance, MistakeTag, Problem, Skeleton, StoredValue } from '../types/problem'
import { gradeLatex, matchesLatex } from './grade'
import { fillTemplate } from './template'

export type AnswerResult =
  | { kind: 'correct' }
  | { kind: 'invalid'; message: string }
  | { kind: 'wrong'; feedback?: string; mistakeTag?: MistakeTag }

export type SkeletonResult = AnswerResult & {
  /** Slots whose value differs from the expected one; shown as hints, not used for the verdict. */
  wrongSlots: string[]
}

/** Finds the first known mistake the answer matches, with its feedback filled in for this instance. */
function recognise(latex: string, mistakes: CommonWrong[], vars: Record<string, string>) {
  const known = mistakes.find((mistake) => matchesLatex(latex, fillTemplate(mistake.latex, vars)))
  return known && { feedback: fillTemplate(known.feedback, vars), mistakeTag: known.mistake_tag }
}

/** Grades the learner's full expression, naming the mistake when it's a recognised one. */
export function gradeFreeAnswer(latex: string, problem: Problem, instance: Instance): AnswerResult {
  const result = gradeLatex(latex, instance.values.answer)
  if (result.kind !== 'wrong') return result
  return { kind: 'wrong', ...recognise(latex, problem.answer.common_wrong, instance.vars) }
}

function storedLatex(value: StoredValue): string {
  if (value.type === 'real') return String(value.approx)
  const [numerator, denominator] = value.exact.split('/')
  return denominator ? `\\frac{${numerator}}{${denominator}}` : numerator
}

/** Builds the gradeable LaTeX for a filled skeleton by substituting each [slot] marker. */
export function skeletonLatex(skeleton: Skeleton, slotValues: Record<string, string>): string {
  return skeleton.parts
    .map((part) => ('op' in part ? part.op.latex : part.group.latex))
    .join('')
    .replace(/\[(\w+)\]/g, (_, slot: string) => `{${slotValues[slot] ?? ''}}`)
}

/**
 * Grades a filled Help skeleton. The verdict is decided by the whole expression's value (so a
 * swapped but equal C(8,5) counts); mismatched slots are returned separately as hints.
 */
export function gradeSkeleton(slotValues: Record<string, string>, problem: Problem, instance: Instance): SkeletonResult {
  const { skeleton } = problem.answer
  const slotIds = skeleton.slots
  if (slotIds.some((slot) => (slotValues[slot] ?? '').trim() === '')) {
    return { kind: 'invalid', message: 'Fill in every box.', wrongSlots: [] }
  }

  const differingSlots = new Set<string>()
  for (const slot of slotIds) {
    const slotResult = gradeLatex(slotValues[slot], instance.values[`slot.${slot}`])
    if (slotResult.kind === 'invalid') return { kind: 'invalid', message: 'Use numbers in the boxes.', wrongSlots: [slot] }
    if (slotResult.kind === 'wrong') differingSlots.add(slot)
  }

  const result = gradeLatex(skeletonLatex(skeleton, slotValues), instance.values.answer)
  if (result.kind !== 'wrong') return { ...result, wrongSlots: [] }

  // Only blame slots in groups whose value is actually wrong: C(8,5) equals C(8,3), so a 5 there is fine.
  const expectedSlots = Object.fromEntries(slotIds.map((slot) => [slot, storedLatex(instance.values[`slot.${slot}`])]))
  const wrongSlots = skeleton.parts.flatMap((part) => {
    if ('op' in part) return []
    const groupSlots = [...part.group.latex.matchAll(/\[(\w+)\]/g)].map((m) => m[1])
    const fill = (values: Record<string, string>) => part.group.latex.replace(/\[(\w+)\]/g, (_, s: string) => `{${values[s]}}`)
    return matchesLatex(fill(slotValues), fill(expectedSlots)) ? [] : groupSlots.filter((s) => differingSlots.has(s))
  })

  for (const mistake of skeleton.slot_mistakes) {
    if (!wrongSlots.includes(mistake.slot)) continue
    if (matchesLatex(slotValues[mistake.slot], fillTemplate(mistake.latex, instance.vars))) {
      return { kind: 'wrong', feedback: fillTemplate(mistake.feedback, instance.vars), mistakeTag: mistake.mistake_tag, wrongSlots }
    }
  }
  return { kind: 'wrong', wrongSlots }
}
