// Turns an answer's markdown into safe HTML with two kinds of annotation:
//  - [n] step references become buttons that jump to plan step n
//  - numbers are wrapped in <span class="num"> and classed as grounded or
//    ungrounded using the server's grounding result (same ignore rules as
//    analyst/grounding.py: integers 0–10, years 1900–2100, numbers in the question)
import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({ gfm: true, breaks: false })

// Mirrors analyst/grounding.py: optional sign, $, thousands separators, decimals, %, and k/M/bn suffixes.
const NUM_RE = /(?<![\w.])([-−]?)(\$?)(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(\s?%)?(?:\s?(k|K|M|B|bn|million|billion|thousand)\b)?/g
const DATE_RE = /\b\d{4}-\d{1,2}(?:-\d{1,2})?(?:[ T]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?\b/g
const SUFFIX = { k: 1e3, K: 1e3, thousand: 1e3, M: 1e6, million: 1e6, B: 1e9, bn: 1e9, billion: 1e9 }
const REF_RE = /\[(\d{1,2})\]/g

export function sig2(v) {
  if (!Number.isFinite(v) || v === 0) return 0
  return Number(v.toPrecision(2))
}

export function parseNumberToken(sign, int, frac, suffix) {
  let v = parseFloat(int.replace(/,/g, '') + (frac || ''))
  if (suffix) v *= SUFFIX[suffix]
  return sign ? -v : v
}

/** Numbers in `text` the way the server's grounding check reads them (dates and [n] refs excluded). */
export function numberTokens(text) {
  const skip = [...text.matchAll(DATE_RE), ...text.matchAll(REF_RE)].map((m) => [m.index, m.index + m[0].length])
  const out = []
  for (const m of text.matchAll(NUM_RE)) {
    const start = m.index, end = m.index + m[0].length
    if (skip.some(([s, e]) => start < e && end > s)) continue
    out.push({ start, end, raw: m[0], value: parseNumberToken(m[1], m[3], m[4], m[6]) })
  }
  return out
}

function ignored(v, raw) {
  const isInt = Number.isInteger(v) && !raw.includes('.')
  if (isInt && Math.abs(v) <= 10) return true
  if (isInt && v >= 1900 && v <= 2100) return true
  return false
}

export function numbersIn(text) {
  const out = []
  for (const { raw, value } of numberTokens(String(text || ''))) {
    if (!ignored(value, raw)) out.push(value)
  }
  return out
}

/**
 * @param {string} md
 * @param {{ungrounded?: number[]|null, question?: string, steps?: number}} opts
 *   ungrounded === null/undefined → grounding not yet known (numbers stay neutral)
 */
export function renderAnswer(md, { ungrounded, question = '', steps = 0 } = {}) {
  const clean = DOMPurify.sanitize(marked.parse(md || ''), { USE_PROFILES: { html: true } })
  if (typeof DOMParser === 'undefined') return clean
  const doc = new DOMParser().parseFromString(`<div id="r">${clean}</div>`, 'text/html')
  const root = doc.getElementById('r')
  const known = Array.isArray(ungrounded)
  const bad = new Set((ungrounded || []).map((v) => sig2(Number(v))))
  const fromQuestion = new Set(numbersIn(question).map(sig2))

  const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const nodes = []
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (n.parentElement.closest('code, pre, a, button')) continue
    nodes.push(n)
  }

  for (const node of nodes) {
    const text = node.nodeValue
    // collect tokens: refs and numbers, in order
    const tokens = []
    for (const m of text.matchAll(REF_RE)) {
      const n = Number(m[1])
      if (n >= 1 && (!steps || n <= steps)) tokens.push({ kind: 'ref', start: m.index, end: m.index + m[0].length, n })
    }
    for (const { start, end, raw, value: v } of numberTokens(text)) {
      if (ignored(v, raw) || fromQuestion.has(sig2(v))) continue
      tokens.push({ kind: 'num', start, end, raw, state: !known ? 'pending' : bad.has(sig2(v)) ? 'ungrounded' : 'grounded' })
    }
    if (!tokens.length) continue
    tokens.sort((a, b) => a.start - b.start)
    const frag = doc.createDocumentFragment()
    let pos = 0
    for (const t of tokens) {
      if (t.start > pos) frag.appendChild(doc.createTextNode(text.slice(pos, t.start)))
      if (t.kind === 'ref') {
        const b = doc.createElement('button')
        b.type = 'button'
        b.className = 'ref'
        b.dataset.step = String(t.n)
        b.setAttribute('aria-label', `Go to step ${t.n}`)
        b.textContent = String(t.n)
        frag.appendChild(b)
      } else {
        const s = doc.createElement('span')
        s.className = `num num-${t.state}`
        s.textContent = t.raw
        if (t.state === 'ungrounded') {
          s.title = 'Not found in any tool result'
          const sr = doc.createElement('span')
          sr.className = 'sr-only'
          sr.textContent = ' (not found in any tool result)'
          s.appendChild(sr)
        }
        frag.appendChild(s)
      }
      pos = t.end
    }
    if (pos < text.length) frag.appendChild(doc.createTextNode(text.slice(pos)))
    node.parentNode.replaceChild(frag, node)
  }
  return root.innerHTML
}

export function renderPlain(md) {
  return DOMPurify.sanitize(marked.parse(md || ''), { USE_PROFILES: { html: true } })
}
