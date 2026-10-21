import { Fragment } from 'react'
import { Tex } from './Tex'

/** Text with $…$ math segments, each rendered with KaTeX (lessons write math this way). */
export function RichText({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\$[^$]*\$)/).map((part, i) =>
        part.startsWith('$') && part.endsWith('$') && part.length > 1 ? (
          <Tex key={i} latex={part.slice(1, -1)} />
        ) : (
          <Fragment key={i}>{part}</Fragment>
        ),
      )}
    </>
  )
}
