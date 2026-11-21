import { useState } from 'react'
import { ChevronDown, CircleDot } from 'lucide-react'
import ColumnCard from './ColumnCard.jsx'
import { fmtInt } from '../lib/format.js'

export default function Brief({ session, onAsk, disabled, canAsk = () => true, compact, folded }) {
  const { profile, understanding: u, understandStatus, dataset } = session
  const [colsOpen, setColsOpen] = useState(!compact)
  const [open, setOpen] = useState(!folded)
  const rows = profile?.row_count ?? dataset?.rows
  const cols = profile?.columns || []
  const pending = !u && understandStatus === 'streaming'
  return (
    <section className="brief" aria-labelledby="brief-title" aria-busy={pending}>
      <p className="eyebrow">Dataset brief{u?.domain && u.domain.toLowerCase() !== 'unknown' ? ` · ${u.domain}` : ''}</p>
      <h1 id="brief-title" className="brief-title">{u?.title || dataset?.name || 'Your dataset'}</h1>
      {dataset?.name && dataset.name !== (u?.title || dataset?.name) ? <p className="brief-file mono">{dataset.name}</p> : null}

      <dl className="brief-stats tnum">
        <div><dt>rows</dt><dd>{fmtInt(rows)}</dd></div>
        <div><dt>columns</dt><dd>{fmtInt(profile?.column_count ?? dataset?.columns)}</dd></div>
        <div><dt>duplicate rows</dt><dd>{fmtInt(profile?.duplicate_rows ?? 0)}</dd></div>
      </dl>

      {folded && (
        <button type="button" className="btn btn-secondary brief-more" aria-expanded={open} aria-controls="brief-rest" onClick={() => setOpen((v) => !v)}>
          {open ? 'Hide the dataset brief' : 'Show the dataset brief'}
          <ChevronDown aria-hidden="true" size={16} className="brief-chev" />
        </button>
      )}
      <div id="brief-rest" className="brief-rest" hidden={!open}>
      <div aria-live="polite">
        {pending && (
          <div className="brief-pending">
            <span className="spinner" aria-hidden="true" />
            <span>Reading the profile and writing a description…</span>
          </div>
        )}
        {understandStatus === 'error' && (
          <p className="brief-error" role="alert">{session.understandError || 'Could not describe this dataset.'} The profile below is still accurate.</p>
        )}
      </div>

      {pending ? (
        <div className="brief-skel" aria-hidden="true"><span /><span /><span style={{ width: '62%' }} /></div>
      ) : u?.summary ? <p className="brief-summary">{u.summary}</p> : null}

      {u?.suggested_questions?.length > 0 && (
        <div className="brief-block">
          <h2 className="brief-h">Questions worth asking</h2>
          <ul className="chips chips-stack">
            {u.suggested_questions.map((q) => (
              <li key={q}><button type="button" className="chip" disabled={disabled || !canAsk(q)} title={canAsk(q) ? undefined : 'Not in this recording'} onClick={() => onAsk(q)}>{q}<span aria-hidden="true" className="chip-arrow">→</span></button></li>
            ))}
          </ul>
        </div>
      )}

      {u?.quality_notes?.length > 0 && (
        <div className="brief-block">
          <h2 className="brief-h">Data quality</h2>
          <ul className="quality">
            {u.quality_notes.map((n) => (<li key={n}><CircleDot aria-hidden="true" size={14} strokeWidth={1.75} /><span>{n}</span></li>))}
          </ul>
        </div>
      )}

      <div className="brief-block">
        <button type="button" className="brief-h brief-toggle" aria-expanded={colsOpen} aria-controls="brief-cols" onClick={() => setColsOpen((v) => !v)}>
          Columns <span className="brief-count tnum">{cols.length}</span>
          <ChevronDown aria-hidden="true" size={16} className="brief-chev" />
        </button>
        <ul id="brief-cols" className="cols" hidden={!colsOpen}>
          {cols.map((c) => <ColumnCard key={c.name} col={c} note={u?.column_notes?.[c.name]} rows={rows} />)}
        </ul>
      </div>
      </div>
    </section>
  )
}
