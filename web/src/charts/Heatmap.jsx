import { useState } from 'react'
import Tooltip from './Tooltip.jsx'
import { useWidth, toNum, label, isNum, firstNumericKey, truncate, measureText } from './util.js'
import { fmtNum, humanize } from '../lib/format.js'

const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
const mix = (a, b, t) => { const A = hex(a), B = hex(b); return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})` }
const lum = (a, b, t) => { const A = hex(a), B = hex(b); const c = A.map((v, i) => (v + (B[i] - v) * t) / 255); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] }
const SEQ = ['#EEF6F1', '#0A5E40']
const NEG = '#2A78D6', MID = '#EFEDE7', POS = '#D4571F'

/** Long (x, y, value) or wide (label + numeric columns) → {xs, ys, get} */
export function matrixFrom(rows, x, y, value) {
  const keys = Object.keys(rows[0] || {})
  if (x && y && keys.includes(x) && keys.includes(y)) {
    const v = value && keys.includes(value) ? value : firstNumericKey(rows, [x, y])
    const xs = [], ys = [], m = new Map()
    for (const r of rows) {
      const a = label(r[x]), b = label(r[y])
      if (!xs.includes(a)) xs.push(a)
      if (!ys.includes(b)) ys.push(b)
      m.set(a + '\u0000' + b, toNum(r[v]))
    }
    return { xs, ys, get: (a, b) => m.get(a + '\u0000' + b), valueName: v }
  }
  const rowKey = keys.find((k) => !isNum(rows[0][k])) || keys[0]
  const xs = keys.filter((k) => k !== rowKey && rows.some((r) => isNum(r[k])))
  const ys = rows.map((r) => label(r[rowKey]))
  const byRow = new Map(rows.map((r) => [label(r[rowKey]), r]))
  return { xs, ys, get: (a, b) => toNum(byRow.get(b)?.[a]), valueName: 'value' }
}

export default function Heatmap({ rows, x, y, value, diverging }) {
  const [ref, w] = useWidth()
  const [tip, setTip] = useState(null)
  const { xs, ys, get, valueName } = matrixFrom(rows, x, y, value)
  const all = []
  ys.forEach((b) => xs.forEach((a) => { const v = get(a, b); if (Number.isFinite(v)) all.push(v) }))
  const min = Math.min(...all), max = Math.max(...all)
  const div = diverging ?? (min < 0 && min >= -1 && max <= 1)
  const fill = (v) => {
    if (!Number.isFinite(v)) return { bg: 'var(--paper-2)', dark: false }
    if (div) { const t = Math.min(1, Math.abs(v)); const end = v < 0 ? NEG : POS; return { bg: mix(MID, end, t), dark: lum(MID, end, t) < 0.42 } }
    const t = max === min ? 0.5 : (v - min) / (max - min)
    return { bg: mix(SEQ[0], SEQ[1], t), dark: lum(SEQ[0], SEQ[1], t) < 0.42 }
  }
  const labelW = Math.min(w < 420 ? 84 : 140, Math.max(...ys.map((s) => measureText(s, 12))) + 10)
  const colLabelH = 34
  const cw = Math.max(18, (w - labelW) / Math.max(1, xs.length))
  const ch = Math.min(40, Math.max(22, cw * 0.6))
  const h = colLabelH + ys.length * ch + 4
  const fits = cw > 46
  const rotate = xs.some((s) => measureText(s, 11) > cw - 4)
  const head = rotate ? colLabelH + 26 : colLabelH
  const svgH = h + (rotate ? 26 : 0)

  return (
    <div className="viz" ref={ref}>
      <div className="viz-scale" aria-hidden="true">
        <span className="tnum">{fmtNum(div ? -1 : min)}</span>
        <span className="viz-scale-bar" style={{ background: div ? `linear-gradient(90deg, ${NEG}, ${MID}, ${POS})` : `linear-gradient(90deg, ${SEQ[0]}, ${SEQ[1]})` }} />
        <span className="tnum">{fmtNum(div ? 1 : max)}</span>
        {valueName !== 'value' && <span className="viz-scale-name">{humanize(valueName)}</span>}
      </div>
      <svg width={w} height={svgH} role="group" aria-label={`Heatmap of ${humanize(valueName)}: ${ys.length} rows by ${xs.length} columns`}>
        {xs.map((a, i) => rotate ? (
          <text key={a} transform={`translate(${labelW + i * cw + cw / 2},${head - 6}) rotate(-35)`} className="viz-tick">{truncate(a, 12)}</text>
        ) : (
          <text key={a} x={labelW + i * cw + cw / 2} y={head - 10} className="viz-tick" textAnchor="middle">{truncate(a, 14)}</text>
        ))}
        {ys.map((b, j) => (
          <g key={b}>
            <text x={labelW - 8} y={head + j * ch + ch / 2} className="viz-label" textAnchor="end" dominantBaseline="central">{truncate(b, 16)}</text>
            {xs.map((a, i) => {
              const v = get(a, b)
              const f = fill(v)
              const cx = labelW + i * cw, cy = head + j * ch
              const t = { x: cx + cw / 2, y: cy, title: `${b} × ${a}`, rows: [{ value: fmtNum(v), name: humanize(valueName) }] }
              return (
                <g key={a} className="viz-hit" tabIndex={0} role="img" aria-label={`${b}, ${a}: ${fmtNum(v)}`}
                  onPointerMove={() => setTip(t)} onFocus={() => setTip(t)} onPointerLeave={() => setTip(null)} onBlur={() => setTip(null)}>
                  <rect x={cx + 1} y={cy + 1} width={cw - 2} height={ch - 2} rx="3" fill={f.bg} className="viz-mark" />
                  {fits && Number.isFinite(v) && (
                    <text x={cx + cw / 2} y={cy + ch / 2} textAnchor="middle" dominantBaseline="central" className="viz-cell" fill={f.dark ? '#fff' : '#141412'}>
                      {fmtNum(v)}
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        ))}
      </svg>
      <Tooltip tip={tip} width={w} />
    </div>
  )
}
