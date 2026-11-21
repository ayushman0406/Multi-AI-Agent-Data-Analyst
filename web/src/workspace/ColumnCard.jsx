import { binsFrom } from '../charts/HistChart.jsx'
import { fmtNum, fmtInt } from '../lib/format.js'

const KIND_LABEL = { numeric: 'number', categorical: 'category', datetime: 'date', boolean: 'yes/no', other: 'other' }

function MiniHist({ col }) {
  const bins = binsFrom(col.histogram, null, null)
  if (!bins.length) return null
  const max = Math.max(1, ...bins.map((b) => b.count))
  const w = 100 / bins.length
  return (
    <div className="mini">
      <svg viewBox="0 0 100 28" preserveAspectRatio="none" className="mini-hist" role="img"
        aria-label={`Distribution of ${col.name}: ${bins.length} bins from ${fmtNum(col.min)} to ${fmtNum(col.max)}`}>
        {bins.map((b, i) => {
          const h = Math.max(b.count > 0 ? 1.5 : 0, (b.count / max) * 28)
          return <rect key={i} x={i * w + 0.4} y={28 - h} width={Math.max(0.5, w - 0.8)} height={h} rx="0.6" />
        })}
      </svg>
      <div className="mini-range tnum"><span>{fmtNum(col.min)}</span><span>median {fmtNum(col.median)}</span><span>{fmtNum(col.max)}</span></div>
    </div>
  )
}

function TopValues({ col, rows }) {
  const tv = col.top_values || []
  if (!tv.length) return null
  const max = Math.max(1, ...tv.map((t) => t.count))
  return (
    <ul className="mini-top" aria-label={`Most common values of ${col.name}`}>
      {tv.slice(0, 5).map((t) => (
        <li key={String(t.value)}>
          <span className="mini-top-label">{t.value === null ? 'null' : String(t.value)}</span>
          <span className="mini-top-bar" aria-hidden="true"><span style={{ width: `${(t.count / max) * 100}%` }} /></span>
          <span className="mini-top-n tnum">{rows ? `${((t.count / rows) * 100).toFixed(0)}%` : fmtInt(t.count)}</span>
        </li>
      ))}
    </ul>
  )
}

export default function ColumnCard({ col, note, rows }) {
  const nullPct = typeof col.null_pct === 'number' ? col.null_pct : rows ? (col.null_count / rows) * 100 : 0
  return (
    <li className="col">
      <div className="col-head">
        <code className="col-name">{col.name}</code>
        <span className={`kind kind-${col.kind}`}>{KIND_LABEL[col.kind] || col.kind}</span>
      </div>
      {note && <p className="col-note">{note}</p>}
      {col.kind === 'numeric' && <MiniHist col={col} />}
      {(col.kind === 'categorical' || col.kind === 'boolean') && <TopValues col={col} rows={rows} />}
      {col.kind === 'datetime' && col.min && (
        <p className="col-range mono tnum">{String(col.min).slice(0, 10)} → {String(col.max).slice(0, 10)}</p>
      )}
      <dl className="col-meta tnum">
        <div><dt>distinct</dt><dd>{fmtInt(col.distinct_count)}</dd></div>
        <div className={nullPct > 0 ? 'has-null' : ''}><dt>empty</dt><dd>{nullPct > 0 ? `${nullPct < 0.1 ? '<0.1' : nullPct.toFixed(1)}%` : 'none'}</dd></div>
        {col.dtype && <div><dt>type</dt><dd>{String(col.dtype).toLowerCase()}</dd></div>}
      </dl>
    </li>
  )
}
