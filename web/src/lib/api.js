import { HttpError, errorText, streamSSE } from './sse.js'

const BASE = '/api'

async function json(path, init) {
  const res = await fetch(BASE + path, init)
  if (!res.ok) throw new HttpError(res.status, await errorText(res))
  return res.json()
}

export const api = {
  health: (signal) => json('/health', { signal }),
  samples: () => json('/samples'),
  getSettings: () => json('/settings'),
  putSettings: (body) => json('/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  demo: () => json('/demo'),
  session: (id) => json(`/sessions/${encodeURIComponent(id)}`),
  createSession({ file, sampleId }) {
    const fd = new FormData()
    if (file) fd.append('file', file)
    else fd.append('sample_id', sampleId)
    return json('/sessions', { method: 'POST', body: fd })
  },
  understand: (id, onEvent, signal) => streamSSE(`${BASE}/sessions/${encodeURIComponent(id)}/understand`, { onEvent, signal }),
  ask: (id, question, onEvent, signal) =>
    streamSSE(`${BASE}/sessions/${encodeURIComponent(id)}/ask`, { method: 'POST', body: JSON.stringify({ question }), onEvent, signal }),
  reportUrl: (id) => `${BASE}/sessions/${encodeURIComponent(id)}/report.md`,
}

export function friendlyError(err) {
  if (err?.name === 'AbortError') return 'Stopped.'
  if (err instanceof HttpError) {
    if (err.status === 413) return `That file is too large for the server. ${err.message}`
    if (err.status === 415) return `That file type isn't supported. Use CSV, TSV, Parquet, JSON or XLSX. ${err.message}`
    if (err.status === 404) return 'The server no longer has this session (it keeps the 20 most recent in memory). Load the dataset again.'
    return `Server error ${err.status}: ${err.message}`
  }
  if (err instanceof TypeError) return 'Could not reach the server. Is it running on port 8000?'
  return err?.message || String(err)
}
