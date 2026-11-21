import { lazy, Suspense } from 'react'
import { Routes, Route, Link } from 'react-router-dom'

const Landing = lazy(() => import('./landing/Landing.jsx'))
const Workspace = lazy(() => import('./workspace/Workspace.jsx'))

function NotFound() {
  return (
    <main className="notfound">
      <p className="eyebrow">404</p>
      <h1>Nothing at this address.</h1>
      <p><Link to="/">Back to the start</Link> or <Link to="/app">open the workspace</Link>.</p>
    </main>
  )
}

export default function App() {
  return (
    <Suspense fallback={<div className="route-loading" aria-busy="true" />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Workspace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}
