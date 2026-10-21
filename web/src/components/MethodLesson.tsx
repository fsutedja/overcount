import { useEffect, useState } from 'react'
import { loadLessons } from '../lib/bank'
import type { Lesson } from '../types/problem'
import { RichText } from './RichText'
import { Tex } from './Tex'

/** A method's "How it works" lesson (DESIGN.md, D6): summary, how, formulas, example, trap. */
export function MethodLesson({ method, compact = false }: { method: string; compact?: boolean }) {
  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadLessons().then(
      (all) => (all.methods[method] ? setLesson(all.methods[method]) : setError('There is no lesson for this method yet.')),
      (e: Error) => setError(e.message),
    )
  }, [method])

  if (error) return <p className="text-ink-muted">{error}</p>
  if (!lesson) return <p className="text-ink-muted">Loading…</p>
  return (
    <article className={`space-y-4 leading-relaxed ${compact ? 'text-[0.95rem]' : ''}`}>
      <p className={compact ? 'font-bold' : 'text-lg'}>
        <RichText text={lesson.summary} />
      </p>
      <section>
        <h2 className="mb-1 font-bold">How it works</h2>
        {lesson.how.map((paragraph, i) => (
          <p key={i} className="mt-2">
            <RichText text={paragraph} />
          </p>
        ))}
      </section>
      <section>
        <h2 className="mb-2 font-bold">Formulas</h2>
        <ul className="space-y-2">
          {lesson.formulas.map((formula) => (
            <li
              key={formula.id}
              className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 rounded-lg border border-border bg-card-sunken px-4 py-2"
            >
              <Tex latex={formula.latex} display className="[&_.katex-display]:my-1" />
              <span className="text-sm text-ink-muted">{formula.when}</span>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="mb-1 font-bold">Example</h2>
        <p className="rounded-lg bg-accent-soft px-4 py-2 text-accent-ink">
          <RichText text={lesson.example} />
        </p>
      </section>
      <section>
        <h2 className="mb-1 font-bold">Watch out</h2>
        <p className="text-ink-muted">
          <RichText text={lesson.trap} />
        </p>
      </section>
    </article>
  )
}
