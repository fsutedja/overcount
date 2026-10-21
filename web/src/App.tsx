import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { HomeRoute } from './pages/HomeRoute'
import { PracticePage } from './pages/PracticePage'
import { ProgressPage } from './pages/ProgressPage'

// Problem pages need the math engine and the math input (most of the bundle), so they load on
// demand; the practice and method pages start without them.
const ProblemRoute = lazy(() => import('./pages/ProblemRoute').then((m) => ({ default: m.ProblemRoute })))
const PreviewRoute = lazy(() => import('./pages/PreviewRoute').then((m) => ({ default: m.PreviewRoute })))
const VisualsGallery = lazy(() => import('./pages/VisualsGallery').then((m) => ({ default: m.VisualsGallery })))

const loading = <p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Loading…</p>

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main>
        <Suspense fallback={loading}>
          <Routes>
            <Route path="/" element={<HomeRoute problemRoute={<ProblemRoute />} />} />
            <Route path="/problem/:id" element={<ProblemRoute />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/progress" element={<ProgressPage />} />
            {import.meta.env.DEV && <Route path="/dev/visuals" element={<VisualsGallery />} />}
            {import.meta.env.DEV && <Route path="/dev/preview/:familyId" element={<PreviewRoute />} />}
            <Route path="*" element={<p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Page not found.</p>} />
          </Routes>
        </Suspense>
      </main>
    </BrowserRouter>
  )
}
