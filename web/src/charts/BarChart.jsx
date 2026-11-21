import { useState } from 'react'
import Tooltip from './Tooltip.jsx'
import { useWidth, label, toNum, seriesColors, linear, measureText, truncate } from './util.js'
import { fmtNum, fmtTick, niceTicks, humanize } from '../lib/format.js'

/** Horizontal bar with a 4px rounded data end and a square baseline end. */
export function hbarPath(x0, x1, y, h, r = 4) {
  const left = Math.min(x0, x1), right = Math.max(x0, x1), w = right - left
  r = Math.min(r, w, h / 2)
  if (w <= 0.5) return ''
  if (x1 >= x0)
    return `M${left},${y}H${right - r}Q${right},${y} ${right},${y + r}V${y + h - r}Q${right},${y + h} ${right - r},${y + h}H${left}Z`
  return `M${right},${y}H${left + r}Q${left},${y} ${left},${y + r}V${y + h - r}Q${left},${y + h} ${left + r},${y + h}H${right}Z`
}

export default function BarChart({ rows, x, y, series, maxBars = 20 }) {
  const [ref, w] = useWidth()
  const [tip, setTip] = useState(null)

  // long format with a series column → grouped
  const cats = []
  const seriesNames = []
  const cell = new Map()
  for (const r of rows) {
    const c = label(r[x])
    const s = series ? label(r[series]) : '_'
    if (!cats.includes(c)) cats.push(c)
    if (!seriesNames.includes(s)) seriesNames.push(s)
    cell.set(c + '\u0000' + s, toNum(r[y]))
  }
  const shown = cats.slice(0, maxBars)
  const colors = seriesColors(seriesNames)
  const grouped = series && seriesNames.length > 1
  const vals = [...cell.values()].filter(Number.isFinite)
  const { lo, hi, ticks } = niceTicks(Math.min(0, ...vals), Math.max(0, ...vals), w < 420 ? 3 : 5)

  const labelW = Math.min(w < 420 ? 96 : 170, Math.max(40, ...shown.map((c) => measureText(c, 12))) + 8)
  const valueRoom = 64
  const plotL = labelW + 8
  const plotR = w - valueRoom
  const sx = linear(lo, hi, plotL, plotR)
  const barH = grouped ? Math.max(6, Math.min(14, 40 / seriesNames.length)) : 18
  const band = grouped ? seriesNames.length * (barH + 2) + 12 : 30
  const top = 8
  const h = top + shown.length * band + 26

  const show = (e, c) => {
    const box = e.currentTarget.ownerSVGElement.getBoundingClientRect()
    const py = (e.clientY ?? box.top + top) - box.top
    setTip({
      x: (e.clientX ?? box.left + plotR) - box.left, y: py, title: c,
      rows: seriesNames.map((s) => ({ color: colors.get(s), value: fmtNum(cell.get(c + '\u0000' + s)), name: grouped ? s : humanize(y) })),
    })
  }
  const showFocus = (e, c, i) => {
    setTip({ x: plotR - 40, y: top + i * band + band / 2, title: c,
      rows: seriesNames.map((s) => ({ color: colors.get(s), value: fmtNum(cell.get(c + '\u0000' + s)), name: grouped ? s : humanize(y) })) })
  }

  return (
    <div className="viz" ref={ref}>
      {grouped && (
        <ul className="viz-legend" aria-label="Legend">
          {seriesNames.map((s) => (
            <li key={s}><span className="viz-swatch" style={{ background: colors.get(s) }} />{s}</li>
          ))}
        </ul>
      )}
      <svg width={w} height={h} role="group" aria-label={`Bar chart of ${humanize(y)} by ${humanize(x)}, ${shown.length} bars`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={sx(t)} x2={sx(t)} y1={top - 4} y2={h - 22} className="viz-grid" />
            <text x={sx(t)} y={h - 6} className="viz-tick" textAnchor="middle">{fmtTick(t, hi)}</text>
          </g>
        ))}
        <line x1={sx(0)} x2={sx(0)} y1={top - 4} y2={h - 22} className="viz-axis" />
        {shown.map((c, i) => {
          const by = top + i * band
          return (
            <g key={c}
              className="viz-hit"
              tabIndex={0}
              role="img"
              aria-label={`${c}: ${seriesNames.map((s) => (grouped ? s + ' ' : '') + fmtNum(cell.get(c + '\u0000' + s))).join(', ')}`}
              onPointerMove={(e) => show(e, c)}
              onPointerLeave={() => setTip(null)}
              onFocus={(e) => showFocus(e, c, i)}
              onBlur={() => setTip(null)}
            >
              <rect x={0} y={by} width={w} height={band} fill="transparent" />
              <text x={labelW} y={by + band / 2} className="viz-label" textAnchor="end" dominantBaseline="central">
                {truncate(c, w < 420 ? 13 : 24)}
              </text>
              {seriesNames.map((s, j) => {
                const v = cell.get(c + '\u0000' + s)
                if (!Number.isFinite(v)) return null
                const yy = grouped ? by + 6 + j * (barH + 2) : by + (band - barH) / 2
                return <path key={s} d={hbarPath(sx(0), sx(v), yy, barH)} fill={colors.get(s)} className="viz-mark" />
              })}
              {!grouped && Number.isFinite(cell.get(c + '\u0000_')) && (
                <text x={Math.max(sx(0), sx(cell.get(c + '\u0000_'))) + 6} y={by + band / 2} className="viz-value" dominantBaseline="central">
                  {fmtNum(cell.get(c + '\u0000_'))}
                </text>
              )}
            </g>
          )
        })}
      </svg>
      {cats.length > shown.length && <p className="viz-note">Showing the first {shown.length} of {cats.length}. The table has all of them.</p>}
      <Tooltip tip={tip} width={w} />
    </div>
  )
}
