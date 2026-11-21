import { useState } from 'react'
import BarChart from './BarChart.jsx'
import LineChart from './LineChart.jsx'
import HistChart from './HistChart.jsx'
import ScatterChart from './ScatterChart.jsx'
import Heatmap from './Heatmap.jsx'
import DataTable from './DataTable.jsx'
import { firstKey, firstNumericKey } from './util.js'
import './charts.css'

const KINDS = { bar: BarChart, line: LineChart, hist: HistChart, histogram: HistChart, scatter: ScatterChart, heatmap: Heatmap }

/** Render a tool result's `chart` spec against its `data` rows, with a table twin. */
export default function Chart({ result, title }) {
  const rows = Array.isArray(result?.data) ? result.data : []
  const spec = result?.chart || {}
  const type = String(spec.type || 'table').toLowerCase()
  const Comp = KINDS[type]
  const [view, setView] = useState(Comp && rows.length ? 'chart' : 'table')
  if (!rows.length) return <p className="viz-note">This step returned no rows.</p>

  const x = spec.x && rows[0] && spec.x in rows[0] ? spec.x : firstKey(rows)
  let y = Array.isArray(spec.y) ? spec.y[0] : spec.y
  if (!y || !(y in rows[0])) y = firstNumericKey(rows, [x])
  const series = spec.series && spec.series in rows[0] ? spec.series : undefined
  const value = spec.value || spec.z
  const caption = title || result?.title || 'Result'

  let body
  try {
    body = view === 'chart' && Comp
      ? <Comp rows={rows} x={x} y={y} series={series} value={value} grain={result?.args?.grain} diverging={result?.tool === 'correlation' ? true : undefined} />
      : <DataTable rows={rows} caption={caption} />
  } catch {
    body = <DataTable rows={rows} caption={caption} />
  }

  return (
    <figure className="viz-figure">
      <div className="viz-head">
        <figcaption className="viz-title">{caption}</figcaption>
        {Comp && (
          <div className="viz-toggle" role="group" aria-label="View as">
            <button type="button" aria-pressed={view === 'chart'} onClick={() => setView('chart')}>Chart</button>
            <button type="button" aria-pressed={view === 'table'} onClick={() => setView('table')}>Table</button>
          </div>
        )}
      </div>
      {body}
    </figure>
  )
}
