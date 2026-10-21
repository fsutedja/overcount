import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { PracticePage } from './pages/PracticePage'
import { ProblemRoute } from './pages/ProblemRoute'

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<ProblemRoute />} />
          <Route path="/problem/:id" element={<ProblemRoute />} />
          <Route path="/practice" element={<PracticePage />} />
          <Route path="*" element={<p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Page not found.</p>} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
