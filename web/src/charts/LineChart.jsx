import { useState } from 'react'
import Tooltip from './Tooltip.jsx'
import { useWidth, label, toNum, seriesColors, linear, truncate } from './util.js'
import { fmtNum, fmtTick, niceTicks, humanize, fmtPeriod } from '../lib/format.js'

export default function LineChart({ rows, x, y, series, grain }) {
  const [ref, w] = useWidth()
  const [hover, setHover] = useState(null)

  const xs = []
  const names = []
  const cell = new Map()
  for (const r of rows) {
    const xv = label(r[x])
    const s = series ? label(r[series]) : humanize(y)
    if (!xs.includes(xv)) xs.push(xv)
    if (!names.includes(s)) names.push(s)
    cell.set(xv + '\u0000' + s, toNum(r[y]))
  }
  const colors = seriesColors(names)
  const vals = [...cell.values()].filter(Number.isFinite)
  const { lo, hi, ticks } = niceTicks(Math.min(0, ...vals), Math.max(...vals), 4)
  const multi = names.length > 1
  const endRoom = names.length <= 4 ? 72 : 12
  const left = 48, top = 12, h = 240, bottom = 28
  const sx = xs.length > 1 ? linear(0, xs.length - 1, left, w - endRoom) : () => (left + w - endRoom) / 2
  const sy = linear(lo, hi, h - bottom, top)
  const every = Math.max(1, Math.ceil(xs.length / Math.max(2, Math.floor((w - left - endRoom) / 78))))

  const tipFor = (i) => {
    if (i === null) return null
    return {
      x: sx(i), y: top + 40, title: fmtPeriod(xs[i], grain),
      rows: names.map((s) => ({ color: colors.get(s), value: fmtNum(cell.get(xs[i] + '\u0000' + s)), name: s })),
    }
  }
  const onMove = (e) => {
    const box = e.currentTarget.getBoundingClientRect()
    const px = e.clientX - box.left
    let best = 0, bd = Infinity
    xs.forEach((_, i) => { const d = Math.abs(sx(i) - px); if (d < bd) { bd = d; best = i } })
    setHover(best)
  }
  const onKey = (e) => {
    if (e.key === 'ArrowRight') { setHover((v) => Math.min(xs.length - 1, v === null ? 0 : v + 1)); e.preventDefault() }
    if (e.key === 'ArrowLeft') { setHover((v) => Math.max(0, v === null ? xs.length - 1 : v - 1)); e.preventDefault() }
    if (e.key === 'Escape') setHover(null)
  }

  return (
    <div className="viz" ref={ref}>
      {multi && (
        <ul className="viz-legend" aria-label="Legend">
          {names.map((s) => (<li key={s}><span className="viz-swatch viz-swatch-line" style={{ background: colors.get(s) }} />{s}</li>))}
        </ul>
      )}
      <svg
        width={w} height={h} tabIndex={0} className="viz-focusable"
        role="group"
        aria-label={`Line chart of ${humanize(y)} over ${humanize(x)}, ${xs.length} points from ${fmtPeriod(xs[0], grain)} to ${fmtPeriod(xs.at(-1), grain)}. Use left and right arrow keys to read values.`}
        onPointerMove={onMove} onPointerLeave={() => setHover(null)} onKeyDown={onKey} onBlur={() => setHover(null)}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={left} x2={w - endRoom + 4} y1={sy(t)} y2={sy(t)} className={t === 0 ? 'viz-axis' : 'viz-grid'} />
            <text x={left - 8} y={sy(t)} className="viz-tick" textAnchor="end" dominantBaseline="central">{fmtTick(t, hi)}</text>
          </g>
        ))}
        {xs.map((xv, i) => (i % every === 0 || i === xs.length - 1) && (i === xs.length - 1 || xs.length - 1 - i >= every * 0.6) ? (
          <text key={xv} x={sx(i)} y={h - 8} className="viz-tick" textAnchor={i === 0 && xs.length > 1 ? 'start' : i === xs.length - 1 && xs.length > 1 ? 'end' : 'middle'}>{truncate(fmtPeriod(xv, grain), 11)}</text>
        ) : null)}
        {names.map((s) => {
          const pts = xs.map((xv, i) => [sx(i), cell.get(xv + '\u0000' + s)]).filter((p) => Number.isFinite(p[1]))
          if (!pts.length) return null
          const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${sy(p[1]).toFixed(1)}`).join('')
          const last = pts.at(-1)
          return (
            <g key={s}>
              {!multi && (
                <path d={`${d}L${last[0]},${sy(Math.max(lo, 0))}L${pts[0][0]},${sy(Math.max(lo, 0))}Z`} fill={colors.get(s)} opacity="0.08" />
              )}
              <path d={d} fill="none" stroke={colors.get(s)} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
              <circle cx={last[0]} cy={sy(last[1])} r="4" fill={colors.get(s)} stroke="var(--surface)" strokeWidth="2" />
              {names.length <= 4 && (
                <text x={last[0] + 8} y={sy(last[1])} className="viz-value" dominantBaseline="central">{fmtTick(last[1], hi)}</text>
              )}
            </g>
          )
        })}
        {hover !== null && (
          <g pointerEvents="none">
            <line x1={sx(hover)} x2={sx(hover)} y1={top} y2={h - bottom} className="viz-crosshair" />
            {names.map((s) => {
              const v = cell.get(xs[hover] + '\u0000' + s)
              return Number.isFinite(v) ? <circle key={s} cx={sx(hover)} cy={sy(v)} r="4" fill={colors.get(s)} stroke="var(--surface)" strokeWidth="2" /> : null
            })}
          </g>
        )}
      </svg>
      <Tooltip tip={tipFor(hover)} width={w} />
    </div>
  )
}
