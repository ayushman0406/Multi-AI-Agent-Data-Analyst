const nf0 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const nf1 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 })
const nf2 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 })
const nf4 = new Intl.NumberFormat('en-US', { maximumSignificantDigits: 4 })

export function fmtNum(v) {
  if (v === null || v === undefined || v === '') return '—'
  if (typeof v !== 'number') return String(v)
  if (!Number.isFinite(v)) return String(v)
  const a = Math.abs(v)
  if (a >= 1000) return nf0.format(v)
  if (a >= 100) return nf1.format(v)
  if (a >= 1) return nf2.format(v)
  if (a === 0) return '0'
  return nf4.format(v)
}

/** Compact tick format: 0 / 1,000 / 20K / 1.2M */
export function fmtTick(v, max = Math.abs(v)) {
  if (typeof v !== 'number') return String(v)
  const a = Math.abs(v)
  if (max >= 10000) {
    if (a >= 1e9) return nf1.format(v / 1e9) + 'B'
    if (a >= 1e6) return nf1.format(v / 1e6) + 'M'
    if (a >= 1e3) return nf1.format(v / 1e3) + 'K'
    return nf0.format(v)
  }
  return fmtNum(v)
}

export function fmtMs(ms) {
  if (ms === undefined || ms === null) return ''
  if (ms < 1000) return `${Math.round(ms)} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

export function fmtInt(v) {
  return typeof v === 'number' ? nf0.format(v) : (v ?? '—')
}

export function humanize(key) {
  return String(key).replace(/_/g, ' ')
}

/** Nice ticks for a [min,max] domain. */
export function niceTicks(min, max, count = 5) {
  if (min === max) { const d = Math.abs(min) || 1; min -= d / 2; max += d / 2 }
  const span = max - min
  const step0 = span / Math.max(1, count)
  const mag = 10 ** Math.floor(Math.log10(step0))
  const err = step0 / mag
  const step = (err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1) * mag
  const lo = Math.floor(min / step) * step
  const hi = Math.ceil(max / step) * step
  const ticks = []
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(Math.round(v / step) * step)
  return { lo, hi, ticks, step }
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
/** Period labels from time_trend: '2025-04-01' + grain → '2025 Q2' / 'Apr 2025' / '2025'. */
export function fmtPeriod(v, grain) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(v))
  if (!m) return String(v)
  const [, y, mo, d] = m
  if (grain === 'quarter') return `${y} Q${Math.floor((+mo - 1) / 3) + 1}`
  if (grain === 'month') return `${MONTHS[+mo - 1]} ${y}`
  if (grain === 'year') return y
  return `${y}-${mo}-${d}`
}
