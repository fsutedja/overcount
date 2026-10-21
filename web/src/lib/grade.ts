import { ComputeEngine } from '@cortex-js/compute-engine'
import type { StoredValue } from '../types/problem'

/**
 * Grades a learner's answer (LaTeX from MathLive) by value: any expression equal to the
 * expected value is correct, so `C(8,3)`, `P(8,3)/3!` and `56` all count.
 * Rational answers compare exactly; answers involving e compare within a relative tolerance.
 */

export type GradeResult =
  | { kind: 'correct' }
  | { kind: 'wrong' }
  | { kind: 'invalid'; message: string }

const REAL_TOLERANCE = 1e-9
/** Largest n allowed in n!, C(n,k), P(n,k) and the largest |exponent|, so pasted input can't hang the tab. */
const MAX_ARGUMENT = 1000

export const ce = new ComputeEngine()

ce.declare('P', {
  signature: '(integer, integer) -> integer',
  evaluate: ([n, k], { engine }) => {
    const total = BigInt(n.re)
    const picked = BigInt(k.re)
    let result = 1n
    for (let i = 0n; i < picked; i++) result *= total - i
    return engine.number(result)
  },
})

const ALLOWED_FUNCTIONS = new Set([
  'Add',
  'Subtract',
  'Negate',
  'Multiply',
  'Divide',
  'Rational',
  'Power',
  'Sqrt',
  'Exp',
  'Factorial',
  'Binomial',
  'P',
  'Delimiter',
  'Sum',
])
/** Largest number of terms a Σ may have, matching the pipeline's MAX_SUM_TERMS. */
const MAX_SUM_TERMS = 1001
const ALLOWED_SYMBOLS = new Set(['ExponentialE'])

type MathJson = number | string | { num: string } | MathJson[] | Record<string, unknown>

function literalNumber(node: MathJson): number | null {
  if (typeof node === 'number') return node
  if (node && typeof node === 'object' && !Array.isArray(node) && typeof node.num === 'string') {
    return Number(node.num)
  }
  return null
}

const isCountArgument = (value: number | null) =>
  value !== null && Number.isInteger(value) && value >= 0 && value <= MAX_ARGUMENT

function mentions(node: MathJson, names: ReadonlySet<string>): boolean {
  if (typeof node === 'string') return names.has(node)
  return Array.isArray(node) && node.some((child) => mentions(child, names))
}

/**
 * A count argument, or (inside a Σ) an expression in its index such as k or 6 − k. The index's
 * range is limited by the Σ's limits, which are checked separately.
 */
const isCountOrIndex = (arg: MathJson, bound: ReadonlySet<string>) =>
  isCountArgument(literalNumber(arg)) || (bound.size > 0 && mentions(arg, bound) && findProblem(arg, bound) === null)

/** Checks a Σ: ["Sum", body, ["Limits", index, lo, hi]], then its body with the index allowed. */
function findSumProblem(args: MathJson[], bound: ReadonlySet<string>): string | null {
  const [body, limits] = args
  if (!Array.isArray(limits) || limits[0] !== 'Limits' || typeof limits[1] !== 'string') {
    return 'A Σ needs an index and limits, like k = 0 below and n above.'
  }
  const [, index, low, high] = limits as [string, string, MathJson, MathJson]
  const from = literalNumber(low)
  const to = literalNumber(high)
  if (from === null || to === null || !Number.isInteger(from) || !Number.isInteger(to)) {
    return 'The limits of a Σ must be whole numbers.'
  }
  if (to - from + 1 > MAX_SUM_TERMS) return 'That Σ has too many terms to check.'
  return findProblem(body, new Set([...bound, index]))
}

/** Returns a learner-facing message if the expression uses something we don't grade, else null. */
function findProblem(node: MathJson, bound: ReadonlySet<string> = new Set()): string | null {
  if (typeof node === 'string') {
    if (ALLOWED_SYMBOLS.has(node) || bound.has(node)) return null
    if (node === 'Nothing') return 'Enter an answer first.'
    if (node === 'ComplexInfinity') return "That divides by zero. Check the bottom of the fraction."
    return 'Use numbers only, no letters like x.'
  }
  if (!Array.isArray(node)) return null
  const [head, ...args] = node
  if (head === 'Error') return "That expression isn't complete yet. Fill in every box."
  if (typeof head !== 'string' || !ALLOWED_FUNCTIONS.has(head)) {
    return 'Use C(n, k), P(n, k), !, Σ, fractions, powers, and + − × ÷.'
  }
  if (head === 'Sum') return findSumProblem(args, bound)
  if (head === 'Factorial' && !isCountOrIndex(args[0], bound)) {
    return `n! needs a whole number from 0 to ${MAX_ARGUMENT}.`
  }
  if ((head === 'Binomial' || head === 'P') && !args.every((a) => isCountOrIndex(a, bound))) {
    return `${head === 'P' ? 'P' : 'C'}(n, k) needs whole numbers from 0 to ${MAX_ARGUMENT}.`
  }
  if (head === 'Power') {
    const exponent = literalNumber(args[1])
    if (exponent !== null && Math.abs(exponent) > MAX_ARGUMENT) return 'That power is too large to check.'
  }
  for (const arg of args) {
    const problem = findProblem(arg, bound)
    if (problem) return problem
  }
  return null
}

/**
 * Rewrites decimal literals as exact fractions (0.25 → 25/100), so a rounded decimal such as
 * 0.2333 is not accepted as 7/30 while an exact decimal such as 0.5 still equals 1/2.
 */
function exactDecimals(node: MathJson): MathJson {
  if (Array.isArray(node)) return node.map(exactDecimals)
  const value = literalNumber(node)
  if (value === null || Number.isInteger(value)) return node
  const digits = typeof node === 'number' ? String(node) : (node as { num: string }).num
  const [whole, fraction = ''] = digits.replace('-', '').split('.')
  const sign = digits.startsWith('-') ? -1 : 1
  return ['Rational', sign * Number(whole + fraction), 10 ** fraction.length]
}

function expectedExpression(expected: Extract<StoredValue, { type: 'rational' }>) {
  const [numerator, denominator = '1'] = expected.exact.split('/')
  return ce.box(['Rational', Number(numerator), Number(denominator)])
}

/** Replaces every use of a symbol with a number in a MathJSON tree. */
function substitute(node: MathJson, name: string, value: number): MathJson {
  if (node === name) return value
  return Array.isArray(node) ? node.map((child) => substitute(child, name, value)) : node
}

const INDEX_SAMPLES = [0, 1, 2, 3, 4, 5]

/**
 * Grades a blank inside a Σ whose answer is an expression in the index (e.g. 6 − k): both
 * sides are evaluated exactly for k = 0…5 and must agree wherever the expected one is defined.
 * So 6 − k, −k + 6 and (12 − 2k)/2 are all right; k − 6 is wrong.
 */
function gradeIndexed(latex: string, expected: Extract<StoredValue, { type: 'indexed' }>): GradeResult {
  const parsed = ce.parse(latex)
  const bound = new Set([expected.index])
  const problem = parsed.isValid ? findProblem(parsed.json as MathJson, bound) : findProblem(['Error'])
  if (problem) return { kind: 'invalid', message: problem.replace('no letters like x', `only the letter ${expected.index}`) }
  const reference = ce.parse(expected.latex).json as MathJson
  let compared = 0
  for (const k of INDEX_SAMPLES) {
    const want = ce.box(substitute(reference, expected.index, k) as never).evaluate()
    if (!Number.isFinite(want.re)) continue
    const got = ce.box(exactDecimals(substitute(parsed.json as MathJson, expected.index, k)) as never).evaluate()
    if (got.isEqual(want) !== true) return { kind: 'wrong' }
    compared++
  }
  return compared >= 2 ? { kind: 'correct' } : { kind: 'wrong' }
}

export function gradeLatex(latex: string, expected: StoredValue): GradeResult {
  if (latex.trim() === '') return { kind: 'invalid', message: 'Enter an answer first.' }
  if (expected.type === 'indexed') return gradeIndexed(latex, expected)
  const parsed = ce.parse(latex)
  const problem = parsed.isValid ? findProblem(parsed.json as MathJson) : findProblem(['Error'])
  if (problem) return { kind: 'invalid', message: problem }

  if (expected.type === 'rational') {
    const exact = ce.box(exactDecimals(parsed.json as MathJson) as never).evaluate()
    return exact.isEqual(expectedExpression(expected)) === true ? { kind: 'correct' } : { kind: 'wrong' }
  }
  const approx = parsed.evaluate().N().re
  if (!Number.isFinite(approx)) return { kind: 'wrong' }
  const closeEnough = Math.abs(approx - expected.approx) <= REAL_TOLERANCE * Math.max(1, Math.abs(expected.approx))
  return closeEnough ? { kind: 'correct' } : { kind: 'wrong' }
}

/**
 * True when the learner's answer has the same exact value as a reference expression, such as
 * a known common mistake. Used for feedback only, so anything unparseable simply doesn't match.
 */
export function matchesLatex(latex: string, referenceLatex: string): boolean {
  const answer = ce.parse(latex)
  if (!answer.isValid || findProblem(answer.json as MathJson)) return false
  const reference = ce.parse(referenceLatex).evaluate()
  return ce.box(exactDecimals(answer.json as MathJson) as never).evaluate().isEqual(reference) === true
}

/** The computed number, shown as a bonus once the problem is solved. */
export function formatValue(value: StoredValue): string {
  if (value.type === 'real') return value.approx.toPrecision(6)
  if (value.type === 'indexed') return value.latex
  const [numerator, denominator] = value.exact.split('/')
  const pretty = (digits: string) => BigInt(digits).toLocaleString('en-US')
  return denominator ? `${pretty(numerator)}/${pretty(denominator)}` : pretty(numerator)
}
