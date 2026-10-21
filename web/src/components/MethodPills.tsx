import { useEffect, useRef, useState } from 'react'
import { loadIndex } from '../lib/bank'
import { MethodLesson } from './MethodLesson'

/**
 * Method pills on a problem (DESIGN.md, D6), e.g. "Stars and bars ⓘ". Each opens that method's
 * lesson in a side panel (a bottom sheet on phones) without leaving the problem.
 */
export function MethodPills({ methods }: { methods: string[] }) {
  const [names, setNames] = useState<Record<string, string>>({})
  const [open, setOpen] = useState<string | null>(null)

  useEffect(() => {
    loadIndex().then(
      (index) => setNames(Object.fromEntries(index.roadmap.flatMap((n) => n.methods).map((m) => [m.id, m.name]))),
      () => setNames({}),
    )
  }, [])

  const shown = methods.filter((m) => names[m]).slice(0, 2)
  if (!shown.length) return null
  return (
    <>
      <div className="mt-3 flex flex-wrap gap-2">
        {shown.map((method) => (
          <button
            key={method}
            type="button"
            onClick={() => setOpen(method)}
            aria-haspopup="dialog"
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-0.5 text-sm font-bold text-accent-ink hover:bg-card-sunken"
          >
            {names[method]} <span aria-hidden="true">ⓘ</span>
            <span className="sr-only">: how this method works</span>
          </button>
        ))}
      </div>
      {open && <LessonPanel method={open} name={names[open]} onClose={() => setOpen(null)} />}
    </>
  )
}

/** A modal <dialog>: Escape closes it, focus moves in and returns to the pill afterwards. */
function LessonPanel({ method, name, onClose }: { method: string; name: string; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)

  // Open once mounted. No close() on cleanup: it would fire onClose (React's development
  // double-mount would then close the panel at once); removing the element closes it anyway.
  useEffect(() => {
    if (ref.current && !ref.current.open) ref.current.showModal()
  }, [])

  return (
    <dialog
      ref={ref}
      aria-labelledby="lesson-panel-title"
      onClose={onClose}
      // A click on the backdrop lands on the dialog element itself.
      onClick={(event) => event.target === event.currentTarget && ref.current?.close()}
      className="fixed inset-x-0 top-auto bottom-0 m-0 max-h-[85vh] w-full max-w-none overflow-y-auto rounded-t-2xl border border-border bg-bg p-0 text-ink backdrop:bg-bg/70 md:inset-y-0 md:right-0 md:left-auto md:h-full md:max-h-none md:w-[30rem] md:rounded-none md:rounded-l-2xl"
    >
      <div className="sticky top-0 flex items-center justify-between gap-3 border-b border-border bg-bg px-5 py-3">
        <h2 id="lesson-panel-title" className="font-bold text-accent-ink">
          {name} · How it works
        </h2>
        <button
          type="button"
          onClick={() => ref.current?.close()}
          className="rounded-lg px-2 py-1 text-ink-muted hover:bg-card-sunken hover:text-ink"
          aria-label="Close"
        >
          ✕
        </button>
      </div>
      <div className="px-5 py-4">
        <MethodLesson method={method} />
      </div>
    </dialog>
  )
}
