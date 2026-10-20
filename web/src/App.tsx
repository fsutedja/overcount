import { Header } from './components/Header'
import { ProblemView } from './components/ProblemView'
import goldenProblem from './data/golden/committee-mixed.json'
import type { Problem } from './types/problem'

const problem = goldenProblem as Problem

export default function App() {
  return (
    <>
      <Header />
      <main>
        <ProblemView problem={problem} instance={problem.instances[0]} />
      </main>
    </>
  )
}
