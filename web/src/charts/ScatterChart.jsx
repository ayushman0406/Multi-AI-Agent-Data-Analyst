import { useState } from 'react'
import Tooltip from './Tooltip.jsx'
import { useWidth, toNum, linear, label, seriesColors, OTHER } from './util.js'
import { fmtNum, fmtTick, niceTicks, humanize } from '../lib/format.js'

export default function ScatterChart({ rows, x, y, series }) {
  const [ref, w] = useWidth()
  const [hover, setHover] = useState(null)
  const pts = rows.map((r) => ({ x: toNum(r[x]), y: toNum(r[y]), s: series ? label(r[series]) : null, r })).filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y))
  const names = series ? [...new Set(pts.map((p) => p.s))] : []
  // all-pairs palettes validate only for three slots; the rest fold into Other
  const colors = seriesColors(names, 3)
  const legend = names.length > 3 ? [...names.slice(0, 3), 'Other'] : names
  const xt = niceTicks(Math.min(...pts.map((p) => p.x)), Math.max(...pts.map((p) => p.x)), 5)
  const yt = niceTicks(Math.min(...pts.map((p) => p.y)), Math.max(...pts.map((p) => p.y)), 4)
  const left = 48, right = 12, top = 10, h = 260, bottom = 30
  const sx = linear(xt.lo, xt.hi, left, w - right)
  const sy = linear(yt.lo, yt.hi, h - bottom, top)

  const onMove = (e) => {
    const box = e.currentTarget.getBoundingClientRect()
    const px = e.clientX - box.left, py = e.clientY - box.top
    let best = null, bd = 28 * 28
    pts.forEach((p, i) => { const d = (sx(p.x) - px) ** 2 + (sy(p.y) - py) ** 2; if (d < bd) { bd = d; best = i } })
    setHover(best)
  }
  const hp = hover !== null ? pts[hover] : null
  return (
    <div className="viz" ref={ref}>
      {legend.length > 1 && (
        <ul className="viz-legend" aria-label="Legend">
          {legend.map((s) => (<li key={s}><span className="viz-swatch viz-swatch-dot" style={{ background: s === 'Other' ? OTHER : colors.get(s) }} />{s}</li>))}
        </ul>
      )}
      <svg width={w} height={h} role="group" aria-label={`Scatter plot of ${humanize(y)} against ${humanize(x)}, ${pts.length} points`} onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        {yt.ticks.map((t) => (
          <g key={'y' + t}>
            <line x1={left} x2={w - right} y1={sy(t)} y2={sy(t)} className="viz-grid" />
            <text x={left - 8} y={sy(t)} className="viz-tick" textAnchor="end" dominantBaseline="central">{fmtTick(t, Math.abs(yt.hi))}</text>
          </g>
        ))}
        {xt.ticks.map((t) => (
          <text key={'x' + t} x={sx(t)} y={h - 10} className="viz-tick" textAnchor="middle">{fmtTick(t, Math.abs(xt.hi))}</text>
        ))}
        <line x1={left} x2={w - right} y1={h - bottom} y2={h - bottom} className="viz-axis" />
        <text x={w - right} y={h - bottom - 6} className="viz-axis-title" textAnchor="end">{humanize(x)} →</text>
        <text x={left + 4} y={top + 4} className="viz-axis-title" dominantBaseline="hanging">↑ {humanize(y)}</text>
        {pts.map((p, i) => (
          <circle key={i} cx={sx(p.x)} cy={sy(p.y)} r={hover === i ? 5 : 3.5} fill={series ? colors.get(p.s) : 'var(--series-1)'} fillOpacity={hover === i ? 1 : 0.7} stroke="var(--surface)" strokeWidth="1.5" />
        ))}
      </svg>
      <Tooltip width={w} tip={hp && { x: sx(hp.x), y: sy(hp.y), title: hp.s, rows: [{ value: fmtNum(hp.x), name: humanize(x) }, { value: fmtNum(hp.y), name: humanize(y) }] }} />
    </div>
  )
}
