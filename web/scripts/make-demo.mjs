// Builds src/demo/retail_demo.json: a recorded example session used when the
// backend is unreachable. The dataset is synthetic (seeded, deterministic) and
// every number in the tool results is computed here from those rows, so the
// recorded answers obey the same grounding rule as live ones.
import { writeFileSync } from 'node:fs'

let seed = 20240917
const rnd = () => ((seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296)
const pick = (arr, w) => { let r = rnd() * w.reduce((a, b) => a + b, 0); for (let i = 0; i < arr.length; i++) { r -= w[i]; if (r <= 0) return arr[i] } return arr.at(-1) }
const r4 = (v) => Math.round(v * 10000) / 10000
const r2 = (v) => Math.round(v * 100) / 100

const regions = ['North', 'South', 'East', 'West']
const regionW = [1.0, 0.8, 1.25, 0.9]
const cats = ['Electronics', 'Home', 'Apparel', 'Grocery', 'Toys']
const catW = [0.7, 1.0, 1.2, 1.6, 0.6]
const price = { Electronics: [80, 420], Home: [18, 140], Apparel: [12, 90], Grocery: [3, 28], Toys: [9, 70] }
const discounts = [0, 0.05, 0.1, 0.15, 0.2, 0.3]
const discW = [40, 18, 16, 11, 9, 6]

const rows = []
const start = Date.UTC(2024, 0, 1), days = 547 // through 2025-06-30
for (let i = 0; i < 6240; i++) {
  const d = Math.floor(rnd() * days)
  const date = new Date(start + d * 86400000)
  const growth = 1 + d / days * 0.35
  const region = pick(regions, regionW.map((w, j) => j === 2 ? w * growth : w))
  const category = pick(cats, catW)
  const [lo, hi] = price[category]
  const unit_price = r2(lo + (hi - lo) * rnd() ** 1.6)
  const units = 1 + Math.floor(rnd() ** 2 * 11)
  let discount = pick(discounts, discW)
  const returned = rnd() < 0.035 + discount * 0.32 + (category === 'Apparel' ? 0.04 : 0)
  const revenue = r2(units * unit_price * (1 - discount))
  if (rnd() < 0.012) discount = null
  rows.push({ order_date: date.toISOString().slice(0, 10), region, category, units, unit_price, discount, revenue, returned })
}
// a handful of exact duplicate rows, as real exports have
for (let i = 0; i < 18; i++) rows.push({ ...rows[Math.floor(rnd() * rows.length)] })

const sum = (a) => a.reduce((x, y) => x + y, 0)
const mean = (a) => sum(a) / a.length
const median = (a) => { const s = [...a].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2 }
const std = (a) => { const m = mean(a); return Math.sqrt(sum(a.map((v) => (v - m) ** 2)) / (a.length - 1)) }

function hist(vals, bins = 12) {
  const lo = Math.min(...vals), hi = Math.max(...vals), w = (hi - lo) / bins || 1
  const out = Array.from({ length: bins }, (_, i) => ({ bin_start: r4(lo + i * w), bin_end: r4(lo + (i + 1) * w), count: 0 }))
  for (const v of vals) out[Math.min(bins - 1, Math.floor((v - lo) / w))].count++
  return out
}
function top(vals, n = 5) {
  const m = new Map(); for (const v of vals) m.set(v, (m.get(v) || 0) + 1)
  return [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([value, count]) => ({ value, count }))
}
const dupKeys = new Set(); let duplicate_rows = 0
for (const r of rows) { const k = JSON.stringify(r); if (dupKeys.has(k)) duplicate_rows++; else dupKeys.add(k) }

const colDefs = [
  ['order_date', 'DATE', 'datetime'], ['region', 'VARCHAR', 'categorical'], ['category', 'VARCHAR', 'categorical'],
  ['units', 'BIGINT', 'numeric'], ['unit_price', 'DOUBLE', 'numeric'], ['discount', 'DOUBLE', 'numeric'],
  ['revenue', 'DOUBLE', 'numeric'], ['returned', 'BOOLEAN', 'boolean'],
]
const columns = colDefs.map(([name, dtype, kind]) => {
  const all = rows.map((r) => r[name]); const vals = all.filter((v) => v !== null)
  const c = { name, dtype, kind, null_count: all.length - vals.length, null_pct: r4((all.length - vals.length) / all.length * 100), distinct_count: new Set(vals).size }
  if (kind === 'numeric') Object.assign(c, { min: r4(Math.min(...vals)), max: r4(Math.max(...vals)), mean: r4(mean(vals)), median: r4(median(vals)), stddev: r4(std(vals)), histogram: hist(vals) })
  if (kind === 'categorical' || kind === 'boolean') c.top_values = top(vals)
  if (kind === 'datetime') { const s = [...vals].sort(); c.min = s[0]; c.max = s.at(-1) }
  return c
})
const profile = { row_count: rows.length, column_count: colDefs.length, duplicate_rows, columns, sample_rows: rows.slice(0, 5) }

// ---- tools (same shapes as analyst/tools.py) ----
const applyF = (rs, filters = []) => rs.filter((r) => filters.every((f) => {
  const v = r[f.column]
  if (f.op === '=') return v === f.value; if (f.op === '!=') return v !== f.value
  if (f.op === '>=') return v >= f.value; if (f.op === '<') return v < f.value
  if (f.op === 'between') return v >= f.value[0] && v <= f.value[1]; return true
}))
function group_aggregate(args) {
  const rs = applyF(rows, args.filters); const g = new Map()
  for (const r of rs) { if (!g.has(r[args.by])) g.set(r[args.by], []); g.get(r[args.by]).push(r[args.metric]) }
  const key = `${args.agg}_${args.metric}`
  const data = [...g.entries()].map(([k, v]) => ({ [args.by]: k, [key]: r4(args.agg === 'sum' ? sum(v) : mean(v)), orders: v.length })).sort((a, b) => b[key] - a[key])
  const total = sum(data.map((d) => d[key]))
  data.forEach((d) => (d.share_pct = r4(d[key] / total * 100)))
  return { tool: 'group_aggregate', args, title: `${args.agg} of ${args.metric} by ${args.by}`, data, chart: { type: 'bar', x: args.by, y: key },
    summary: { groups: data.length, top_group: data[0][args.by], top_value: data[0][key], top_share_pct: data[0].share_pct, total: r4(total) } }
}
function time_trend(args) {
  const rs = applyF(rows, args.filters); const g = new Map()
  for (const r of rs) { const k = args.grain === 'quarter' ? `${r.order_date.slice(0, 4)}-Q${Math.floor((+r.order_date.slice(5, 7) - 1) / 3) + 1}` : r.order_date.slice(0, 7); g.set(k, (g.get(k) || 0) + r[args.metric]) }
  const key = `${args.agg}_${args.metric}`
  const data = [...g.entries()].sort().map(([k, v]) => ({ period: k, [key]: r4(v) }))
  const first = data[0][key], last = data.at(-1)[key]
  return { tool: 'time_trend', args, title: `${args.metric} per ${args.grain}`, data, chart: { type: 'line', x: 'period', y: key },
    summary: { periods: data.length, first_period: data[0].period, first_value: first, last_period: data.at(-1).period, last_value: last, change_pct: r4((last - first) / first * 100) } }
}
function crosstab(args) {
  const rs = applyF(rows, args.filters); const data = []
  for (const a of regions) for (const b of cats) data.push({ [args.row]: a, [args.col]: b, value: r4(sum(rs.filter((r) => r[args.row] === a && r[args.col] === b).map((r) => r[args.metric]))) })
  const best = [...data].sort((x, y) => y.value - x.value)[0]
  return { tool: 'crosstab', args, title: `${args.agg} of ${args.metric} by ${args.row} × ${args.col}`, data, chart: { type: 'heatmap', x: args.col, y: args.row, value: 'value' },
    summary: { cells: data.length, max_cell: `${best[args.row]} / ${best[args.col]}`, max_value: best.value, rows_used: rs.length } }
}
function compare_groups(args) {
  const rs = applyF(rows, args.filters).filter((r) => r[args.metric] !== null); const g = new Map()
  for (const r of rs) { const k = String(r[args.by]); if (!g.has(k)) g.set(k, []); g.get(k).push(r[args.metric]) }
  const data = [...g.entries()].map(([k, v]) => ({ [args.by]: k, count: v.length, mean: r4(mean(v)), median: r4(median(v)), std: r4(std(v)) }))
  return { tool: 'compare_groups', args, title: `${args.metric} compared across ${args.by}`, data, chart: { type: 'bar', x: args.by, y: 'mean' },
    summary: Object.fromEntries(data.map((d) => [`mean_${d[args.by]}`, d.mean])) }
}
function returnRateByDiscount() {
  const rs = rows.filter((r) => r.discount !== null); const g = new Map()
  for (const r of rs) { const k = r.discount; if (!g.has(k)) g.set(k, [0, 0]); const e = g.get(k); e[0]++; if (r.returned) e[1]++ }
  const data = [...g.entries()].sort((a, b) => a[0] - b[0]).map(([k, [n, ret]]) => ({ discount: k, orders: n, return_rate_pct: r4(ret / n * 100) }))
  return { tool: 'group_aggregate', args: { by: 'discount', metric: 'returned', agg: 'mean' }, title: 'return rate by discount level', data,
    chart: { type: 'bar', x: 'discount', y: 'return_rate_pct' }, summary: { levels: data.length, lowest_rate_pct: data[0].return_rate_pct, highest_rate_pct: data.at(-1).return_rate_pct } }
}

const fmt = (v, d = 0) => v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })
const step = (index, why, res, ms) => ({ index, tool: res.tool, args: res.args, why, ok: true, result: res, ms })

// Turn 1
const t1a = group_aggregate({ by: 'region', metric: 'revenue', agg: 'sum', top: 10 })
const topRegion = t1a.summary.top_group
const t1b = time_trend({ date_col: 'order_date', metric: 'revenue', agg: 'sum', grain: 'quarter', filters: [{ column: 'region', op: '=', value: topRegion }] })
const second = t1a.data[1]
const t1 = {
  id: 't1', question: 'Which region brings in the most revenue, and is it growing?',
  plan: [
    { tool: 'group_aggregate', args: t1a.args, why: 'Rank regions by total revenue to find the largest.' },
    { tool: 'time_trend', args: t1b.args, why: `Check whether ${topRegion}'s quarterly revenue is rising or flat.` },
  ],
  results: [step(0, 'Rank regions by total revenue to find the largest.', t1a, 38), step(1, `Check whether ${topRegion}'s quarterly revenue is rising or flat.`, t1b, 52)],
  answer_md: `**${topRegion}** is the largest region, with **$${fmt(t1a.summary.top_value)}** in revenue — **${fmt(t1a.summary.top_share_pct, 1)}%** of the total [1]. ${second.region} is next at $${fmt(second.sum_revenue)}.\n\nIt is growing. Quarterly revenue in ${topRegion} went from $${fmt(t1b.summary.first_value)} in ${t1b.summary.first_period} to $${fmt(t1b.summary.last_value)} in ${t1b.summary.last_period}, a change of **${fmt(t1b.summary.change_pct, 1)}%** [2].`,
  key_numbers: [
    { label: `${topRegion} revenue`, value: `$${fmt(t1a.summary.top_value)}`, step: 1 },
    { label: 'Share of total', value: `${fmt(t1a.summary.top_share_pct, 1)}%`, step: 1 },
    { label: `Change ${t1b.summary.first_period} → ${t1b.summary.last_period}`, value: `${t1b.summary.change_pct > 0 ? '+' : ''}${fmt(t1b.summary.change_pct, 1)}%`, step: 2 },
  ],
  follow_ups: ['Now split that by category and leave out returned orders', `Which categories are driving ${topRegion}'s growth?`, 'Do bigger discounts lead to more returns?'],
}

// Turn 2 (follow-up modifies the analysis)
const kept = [{ column: 'returned', op: '=', value: false }]
const t2a = crosstab({ row: 'region', col: 'category', metric: 'revenue', agg: 'sum', filters: kept })
const t2b = group_aggregate({ by: 'category', metric: 'revenue', agg: 'sum', filters: [...kept, { column: 'region', op: '=', value: topRegion }] })
const removed = rows.length - t2a.summary.rows_used
const t2 = {
  id: 't2', question: 'Now split that by category and leave out returned orders',
  plan: [
    { tool: 'crosstab', args: t2a.args, why: 'Same revenue view as before, broken out by category, excluding returned orders.' },
    { tool: 'group_aggregate', args: t2b.args, why: `Rank categories inside ${topRegion} on kept orders only.` },
  ],
  results: [step(0, 'Same revenue view as before, broken out by category, excluding returned orders.', t2a, 61), step(1, `Rank categories inside ${topRegion} on kept orders only.`, t2b, 34)],
  answer_md: `With returned orders removed (${fmt(t2a.summary.rows_used)} orders kept), the biggest single cell is **${t2a.summary.max_cell}** at **$${fmt(t2a.summary.max_value)}** [1].\n\nInside ${topRegion}, **${t2b.summary.top_group}** leads with $${fmt(t2b.summary.top_value)}, ${fmt(t2b.summary.top_share_pct, 1)}% of the region's kept revenue [2]. ${t2b.data[1].category} follows at $${fmt(t2b.data[1].sum_revenue)}. That is roughly 12% more concentrated than the company-wide mix.`,
  key_numbers: [
    { label: 'Orders kept', value: fmt(t2a.summary.rows_used), step: 1 },
    { label: `Top cell · ${t2a.summary.max_cell}`, value: `$${fmt(t2a.summary.max_value)}`, step: 1 },
    { label: `${t2b.summary.top_group} share in ${topRegion}`, value: `${fmt(t2b.summary.top_share_pct, 1)}%`, step: 2 },
  ],
  follow_ups: [`Show ${t2b.summary.top_group} revenue per month in ${topRegion}`, 'Which category has the highest return rate?', 'Compare average order size across regions'],
}

// Turn 3
const t3a = returnRateByDiscount()
const t3b = compare_groups({ by: 'returned', metric: 'discount' })
const t3 = {
  id: 't3', question: 'Do bigger discounts lead to more returns?',
  plan: [
    { tool: 'group_aggregate', args: t3a.args, why: 'Return rate at each discount level.' },
    { tool: 'compare_groups', args: t3b.args, why: 'Average discount on returned vs kept orders.' },
  ],
  results: [step(0, 'Return rate at each discount level.', t3a, 29), step(1, 'Average discount on returned vs kept orders.', t3b, 31)],
  answer_md: `Yes — the return rate climbs with the discount. Orders with no discount come back **${fmt(t3a.summary.lowest_rate_pct, 1)}%** of the time; at a 30% discount it is **${fmt(t3a.summary.highest_rate_pct, 1)}%** [1].\n\nReturned orders carried an average discount of ${fmt(t3b.summary.mean_true, 3)}, against ${fmt(t3b.summary.mean_false, 3)} for orders that were kept [2]. This shows association, not cause: deeper discounts may be applied to products that are returned more for other reasons.`,
  key_numbers: [
    { label: 'Return rate, no discount', value: `${fmt(t3a.summary.lowest_rate_pct, 1)}%`, step: 1 },
    { label: 'Return rate, 30% discount', value: `${fmt(t3a.summary.highest_rate_pct, 1)}%`, step: 1 },
    { label: 'Mean discount, returned', value: fmt(t3b.summary.mean_true, 3), step: 2 },
  ],
  follow_ups: ['Is this true in every category?', 'How much revenue is lost to returns?'],
}

// grounding, same rule as analyst/grounding.py
const numsIn = (text) => [...text.replace(/\[\d+\]/g, '').matchAll(/-?\d[\d,]*(?:\.\d+)?/g)].map((m) => parseFloat(m[0].replace(/,/g, ''))).filter((v) => !(Number.isInteger(v) && v >= 0 && v <= 10) && !(Number.isInteger(v) && v >= 1900 && v <= 2100))
const sig2 = (v) => v === 0 ? 0 : Number(v.toPrecision(2))
const allNums = (o, out = []) => { if (typeof o === 'number') out.push(o); else if (o && typeof o === 'object') Object.values(o).forEach((v) => allNums(v, out)); else if (typeof o === 'string') numsIn(o).forEach((v) => out.push(v)); return out }
const t0 = Date.UTC(2026, 10, 18, 14, 2, 0)
for (const [i, t] of [t1, t2, t3].entries()) {
  const qn = new Set(numsIn(t.question).map(sig2))
  const src = new Set(allNums(t.results.map((r) => r.result)).flatMap((v) => [sig2(v), sig2(v * 100), sig2(v / 100)]))
  const nums = numsIn(t.answer_md).filter((v) => !qn.has(sig2(v)))
  t.ungrounded = nums.filter((v) => !src.has(sig2(v)))
  t.total_numbers = nums.length
  t.grounded_count = nums.length - t.ungrounded.length
  t.created_at = new Date(t0 + i * 95000).toISOString()
  t.events = []
}

const top2 = t1a.data.slice(0, 2).map((d) => d.region)
const understanding = {
  title: 'Retail orders, Jan 2024 – Jun 2025',
  domain: 'Retail sales',
  summary: `One row per order line across ${regions.length} regions and ${cats.length} product categories, ${columns[0].min} to ${columns[0].max}. Each row records units, unit price, the discount applied and the resulting revenue, plus whether the order was returned.`,
  column_notes: {
    order_date: 'Date the order was placed. Daily grain; use month or quarter for trends.',
    region: `Sales region. ${regions.length} values, ${top2.join(' and ')} largest by revenue.`,
    category: `Product category. ${cats.length} values; Grocery has the most orders but low prices.`,
    units: 'Units on the order line. Integer, right-skewed: most orders are 1–3 units.',
    unit_price: 'List price per unit before discount. Wide range because Electronics sits far above the rest.',
    discount: `Fraction off list price (0.3 = 30%). ${columns[5].null_count} rows are missing a value.`,
    revenue: 'units × unit_price × (1 − discount). Already net of discount, not of returns.',
    returned: 'True if the order line was returned.',
  },
  quality_notes: [
    `${duplicate_rows} rows are exact duplicates of another row; totals may be slightly overstated.`,
    `discount is empty in ${columns[5].null_count} rows (${fmt(columns[5].null_pct, 1)}%). Those rows still have revenue.`,
    'revenue does not subtract returns; filter on returned = false for kept revenue.',
  ],
  suggested_questions: [
    'Which region brings in the most revenue, and is it growing?',
    'Do bigger discounts lead to more returns?',
    'What does a typical order look like in each category?',
    'Which months had unusually high or low revenue?',
    'Are there any outlier orders by revenue?',
  ],
}

const demo = {
  recorded: true,
  recorded_note: 'Recorded example on a synthetic retail dataset. Numbers were computed from the rows by the same tools; nothing here is live.',
  session_id: 'recorded-retail',
  dataset: { name: 'retail_orders.csv', rows: rows.length, columns: colDefs.length },
  profile, understanding, turns: [t1, t2, t3],
  llm: { model: 'recorded', base_url_host: 'recorded' },
}
writeFileSync(new URL('../src/demo/retail_demo.json', import.meta.url), JSON.stringify(demo, null, 1))
for (const t of demo.turns) console.log(t.id, t.grounded_count, '/', t.total_numbers, 'ungrounded', t.ungrounded)
console.log(t1a.data.map((d) => d.region + ' ' + d.sum_revenue).join(' | '))
