import { useEffect, useRef, useState } from 'react'

export const SERIES = ['var(--series-1)', 'var(--series-2)', 'var(--series-3)', 'var(--series-4)', 'var(--series-5)', 'var(--series-6)']
export const OTHER = '#A8A59C'

export function useWidth(initial = 600) {
  const ref = useRef(null)
  const [w, setW] = useState(initial)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const set = () => setW(Math.max(240, Math.floor(el.getBoundingClientRect().width)))
    set()
    if (typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(set)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return [ref, w]
}

export const isNum = (v) => typeof v === 'number' && Number.isFinite(v)
export const toNum = (v) => (isNum(v) ? v : typeof v === 'string' && v.trim() !== '' && !isNaN(+v) ? +v : typeof v === 'boolean' ? +v : NaN)
export const label = (v) => (v === null || v === undefined ? '(empty)' : typeof v === 'boolean' ? String(v) : String(v))

/** Pick a numeric column other than the excluded ones. */
export function firstNumericKey(rows, exclude = []) {
  const keys = Object.keys(rows[0] || {})
  return keys.find((k) => !exclude.includes(k) && rows.some((r) => isNum(r[k])))
}
export function firstKey(rows, exclude = []) {
  return Object.keys(rows[0] || {}).find((k) => !exclude.includes(k))
}

/** Stable series → colour map; order of first appearance, capped, rest folds to Other. */
export function seriesColors(names, cap = SERIES.length) {
  const m = new Map()
  names.forEach((n, i) => m.set(n, i < cap ? SERIES[i] : OTHER))
  return m
}

export function linear(d0, d1, r0, r1) {
  const k = d1 === d0 ? 0 : (r1 - r0) / (d1 - d0)
  return (v) => r0 + (v - d0) * k
}

export function measureText(str, px = 11) {
  // monospace-ish estimate good enough for layout decisions
  return String(str).length * px * 0.6
}

export function truncate(str, n) {
  const s = String(str)
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}
