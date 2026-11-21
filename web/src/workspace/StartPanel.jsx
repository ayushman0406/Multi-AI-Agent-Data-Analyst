import { useEffect, useRef, useState } from 'react'
import { FileUp, PlayCircle } from 'lucide-react'
import { api } from '../lib/api.js'
import { fmtInt } from '../lib/format.js'

const TYPES = ['.csv', '.tsv', '.parquet', '.json', '.xlsx']

export default function StartPanel({ serverUp, onOpen, onRecording, loading, error }) {
  const [samples, setSamples] = useState(null)
  const [drag, setDrag] = useState(false)
  const [localErr, setLocalErr] = useState(null)
  const input = useRef(null)

  useEffect(() => {
    if (!serverUp) return
    api.samples().then(setSamples).catch(() => setSamples([]))
  }, [serverUp])

  const take = (file) => {
    if (!file) return
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!TYPES.includes(ext)) { setLocalErr(`${file.name} is not a supported type. Use ${TYPES.join(', ')}.`); return }
    if (file.size > 25 * 1024 * 1024) { setLocalErr(`${file.name} is ${(file.size / 1048576).toFixed(1)} MB. The server accepts up to 25 MB.`); return }
    setLocalErr(null)
    onOpen({ file, label: file.name })
  }

  return (
    <div className="start">
      <div className="start-lead">
        <p className="eyebrow">Workspace</p>
        <h1 className="start-title">Start with a dataset.</h1>
        <p className="start-sub">It will be profiled in DuckDB, described in plain language, and then you can ask it questions. Files stay on your server, in memory, and are deleted when the session ends.</p>

        <div
          className={`drop${drag ? ' is-drag' : ''}${!serverUp ? ' is-off' : ''}`}
          onDragOver={(e) => { e.preventDefault(); if (serverUp) setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); if (serverUp) take(e.dataTransfer.files?.[0]) }}
        >
          <FileUp size={22} strokeWidth={1.5} aria-hidden="true" />
          <p className="drop-main">Drop a file here, or <button type="button" className="linklike" disabled={!serverUp || !!loading} onClick={() => input.current?.click()}>choose one</button></p>
          <p className="drop-sub mono">CSV · TSV · Parquet · JSON · XLSX — up to 25 MB, 200,000 rows</p>
          <input ref={input} type="file" accept={TYPES.join(',')} hidden onChange={(e) => take(e.target.files?.[0])} />
        </div>
        <div aria-live="assertive">
          {(localErr || error) && <p className="form-error">{localErr || error}</p>}
          {loading && <p className="start-loading"><span className="spinner" aria-hidden="true" /> Loading {loading}…</p>}
        </div>
      </div>

      <div className="start-side">
        <h2 className="eyebrow">Sample datasets</h2>
        {!serverUp ? (
          <p className="start-muted">Samples are served by the backend, which isn't reachable right now.</p>
        ) : samples === null ? (
          <p className="start-muted"><span className="spinner" aria-hidden="true" /> Loading samples…</p>
        ) : samples.length === 0 ? (
          <p className="start-muted">The server has no samples in <code>samples/</code>.</p>
        ) : (
          <ul className="samples">
            {samples.map((s) => (
              <li key={s.id}>
                <button type="button" className="sample" disabled={!!loading} onClick={() => onOpen({ sampleId: s.id, label: s.name })}>
                  <span className="sample-name">{s.name}</span>
                  {s.description && <span className="sample-desc">{s.description}</span>}
                  <span className="sample-meta mono tnum">{fmtInt(s.rows)} rows · {fmtInt(s.columns)} columns</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="recorded-card">
          <h2 className="eyebrow">Or watch one first</h2>
          <button type="button" className="sample sample-recorded" onClick={onRecording} disabled={!!loading}>
            <span className="sample-name"><PlayCircle size={16} aria-hidden="true" /> Example session: retail orders</span>
            <span className="sample-desc">Three questions on the retail sample, replayed step by step. The tool results are real; the answer text was written by hand to show the format, and nothing is computed live.</span>
          </button>
        </div>
      </div>
    </div>
  )
}
