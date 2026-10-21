import type { ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { HomePage } from './HomePage'

/** "/" is Home; the old "/?p=<id>" links still open that problem. */
export function HomeRoute({ problemRoute }: { problemRoute: ReactNode }) {
  const [params] = useSearchParams()
  return params.get('p') ? problemRoute : <HomePage />
}
