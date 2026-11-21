import { useState } from 'react'
import { fmtNum, humanize } from '../lib/format.js'
import { isNum } from './util.js'

export default function DataTable({ rows, caption, limit = 12 }) {
  const [all, setAll] = useState(false)
  if (!rows?.length) return <p className="viz-note">No rows.</p>
  const cols = Object.keys(rows[0])
  const numeric = Object.fromEntries(cols.map((c) => [c, rows.some((r) => isNum(r[c]))]))
  const shown = all ? rows : rows.slice(0, limit)
  return (
    <div className="viz-table-wrap">
      <div className="viz-table-scroll" tabIndex={0} role="region" aria-label={caption || 'Result rows'}>
        <table className="viz-table">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead>
            <tr>{cols.map((c) => <th key={c} scope="col" className={numeric[c] ? 'is-num' : ''}>{humanize(c)}</th>)}</tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={i}>
                {cols.map((c) => (
                  <td key={c} className={numeric[c] ? 'is-num' : ''}>
                    {r[c] === null || r[c] === undefined ? <span className="viz-null">null</span> : isNum(r[c]) ? fmtNum(r[c]) : typeof r[c] === 'object' ? JSON.stringify(r[c]) : String(r[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > limit && (
        <button type="button" className="btn btn-quiet viz-more" onClick={() => setAll((v) => !v)}>
          {all ? 'Show fewer rows' : `Show all ${rows.length} rows`}
        </button>
      )}
    </div>
  )
}
