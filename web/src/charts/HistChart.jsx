import { useState } from 'react'
import Tooltip from './Tooltip.jsx'
import { useWidth, toNum, linear, label, isNum } from './util.js'
import { fmtNum, fmtTick, niceTicks, humanize } from '../lib/format.js'

const LO_KEYS = ['bin_start', 'bin_low', 'low', 'lo', 'start', 'left', 'from', 'min']
const HI_KEYS = ['bin_end', 'bin_high', 'high', 'hi', 'end', 'right', 'to', 'max']

/** Normalise histogram rows from a tool or a profile into [{lo, hi, label, count}]. */
export function binsFrom(rows, x, y) {
  if (!Array.isArray(rows) || !rows.length) return []
  if (isNum(rows[0])) return rows.map((c, i) => ({ lo: i, hi: i + 1, label: String(i + 1), count: c }))
  const keys = Object.keys(rows[0])
  const lo = LO_KEYS.find((k) => keys.includes(k))
  const hi = HI_KEYS.find((k) => keys.includes(k))
  const cnt = y && keys.includes(y) ? y : ['count', 'n', 'freq', 'frequency', 'value'].find((k) => keys.includes(k)) || keys.find((k) => isNum(rows[0][k]) && k !== lo && k !== hi)
  return rows.map((r) => {
    const a = lo ? toNum(r[lo]) : NaN, b = hi ? toNum(r[hi]) : NaN
    return { lo: a, hi: b, label: Number.isFinite(a) && Number.isFinite(b) ? `${fmtNum(a)} – ${fmtNum(b)}` : label(r[x] ?? r.bin ?? r.range), count: toNum(r[cnt]) || 0 }
  })
}

export default function HistChart({ rows, x, y }) {
  const [ref, w] = useWidth()
  const [tip, setTip] = useState(null)
  const bins = binsFrom(rows, x, y)
  const max = Math.max(1, ...bins.map((b) => b.count))
  const { hi, ticks } = niceTicks(0, max, 4)
  const left = 44, right = 8, top = 10, h = 220, bottom = 28
  const bw = (w - left - right) / Math.max(1, bins.length)
  const sy = linear(0, hi, h - bottom, top)
  const numeric = bins.every((b) => Number.isFinite(b.lo) && Number.isFinite(b.hi))
  const tickEvery = Math.max(1, Math.ceil(bins.length / Math.floor((w - left) / 64)))

  return (
    <div className="viz" ref={ref}>
      <svg width={w} height={h} role="group" aria-label={`Histogram of ${humanize(x || 'values')}, ${bins.length} bins`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={left} x2={w - right} y1={sy(t)} y2={sy(t)} className={t === 0 ? 'viz-axis' : 'viz-grid'} />
            <text x={left - 8} y={sy(t)} className="viz-tick" textAnchor="end" dominantBaseline="central">{fmtTick(t, hi)}</text>
          </g>
        ))}
        {bins.map((b, i) => {
          const x0 = left + i * bw + 1, bh = sy(0) - sy(b.count), width = Math.max(1, bw - 2)
          const r = Math.min(4, width / 2, bh)
          const d = bh <= 0 ? '' : `M${x0},${sy(0)}V${sy(b.count) + r}Q${x0},${sy(b.count)} ${x0 + r},${sy(b.count)}H${x0 + width - r}Q${x0 + width},${sy(b.count)} ${x0 + width},${sy(b.count) + r}V${sy(0)}Z`
          return (
            <g key={i} className="viz-hit" tabIndex={0} role="img" aria-label={`${b.label}: ${fmtNum(b.count)}`}
              onPointerMove={() => setTip({ x: x0 + width / 2, y: Math.max(top + 20, sy(b.count)), title: b.label, rows: [{ value: fmtNum(b.count), name: 'rows' }] })}
              onFocus={() => setTip({ x: x0 + width / 2, y: Math.max(top + 20, sy(b.count)), title: b.label, rows: [{ value: fmtNum(b.count), name: 'rows' }] })}
              onPointerLeave={() => setTip(null)} onBlur={() => setTip(null)}>
              <rect x={x0 - 1} y={top} width={bw} height={h - bottom - top} fill="transparent" />
              <path d={d} fill="var(--series-1)" className="viz-mark" />
            </g>
          )
        })}
        {numeric
          ? bins.map((b, i) => (i % tickEvery === 0 ? (
            <text key={i} x={left + i * bw} y={h - 8} className="viz-tick" textAnchor={i === 0 ? 'start' : 'middle'}>{fmtTick(b.lo, Math.abs(bins.at(-1).hi))}</text>
          ) : null)).concat(
            <text key="end" x={w - right} y={h - 8} className="viz-tick" textAnchor="end">{fmtTick(bins.at(-1)?.hi, Math.abs(bins.at(-1)?.hi))}</text>,
          )
          : null}
      </svg>
      <Tooltip tip={tip} width={w} />
    </div>
  )
}
