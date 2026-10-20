// Copies MathLive's fonts into public/ so the math editor works offline and without a CDN.
// Runs before `dev` and `build` (see package.json); the output folder is gitignored.
import { cpSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const webDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const mathliveDir = join(webDir, 'node_modules', 'mathlive')
const source = join(mathliveDir, 'fonts')
const target = join(webDir, 'public', 'mathlive', 'fonts')

if (!existsSync(source)) {
  throw new Error(`MathLive fonts not found at ${source}`)
}
cpSync(source, target, { recursive: true })
console.log(`Copied MathLive fonts → ${target}`)
