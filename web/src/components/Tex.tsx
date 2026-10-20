import katex from 'katex'

/** Renders LaTeX with KaTeX. Bad input shows the raw source instead of throwing. */
export function Tex({ latex, className }: { latex: string; className?: string }) {
  const html = katex.renderToString(latex, { throwOnError: false, output: 'htmlAndMathml' })
  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />
}
