import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { PracticePage } from './pages/PracticePage'
import { PreviewRoute } from './pages/PreviewRoute'
import { ProblemRoute } from './pages/ProblemRoute'
import { VisualsGallery } from './pages/VisualsGallery'

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<ProblemRoute />} />
          <Route path="/problem/:id" element={<ProblemRoute />} />
          <Route path="/practice" element={<PracticePage />} />
          {import.meta.env.DEV && <Route path="/dev/visuals" element={<VisualsGallery />} />}
          {import.meta.env.DEV && <Route path="/dev/preview/:familyId" element={<PreviewRoute />} />}
          <Route path="*" element={<p className="mx-auto max-w-5xl px-4 py-8 text-ink-muted">Page not found.</p>} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
