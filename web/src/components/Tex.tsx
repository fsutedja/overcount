import katex from 'katex'

/** Renders LaTeX with KaTeX. Bad input shows the raw source instead of throwing. */
export function Tex({ latex, className, display = false }: { latex: string; className?: string; display?: boolean }) {
  const html = katex.renderToString(latex, { throwOnError: false, output: 'htmlAndMathml', displayMode: display })
  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />
}
