// Everything the landing page shows comes from the recorded session in
// src/demo/retail_demo.json, so the page and the workspace agree.
import demo from '../demo/retail_demo.json'
import { numbersIn, sig2 } from '../lib/answer.js'

export { demo }
export const [turn1, turn2, turn3] = demo.turns

/** Every number in a turn's tool results, with where it came from. */
export function sourceNumbers(turn) {
  const out = []
  const walk = (v, path, step) => {
    if (typeof v === 'number') out.push({ value: v, path, step })
    else if (Array.isArray(v)) v.forEach((x, i) => walk(x, `${path}[${i}]`, step))
    else if (v && typeof v === 'object') Object.entries(v).forEach(([k, x]) => walk(x, path ? `${path}.${k}` : k, step))
  }
  turn.results.forEach((r, i) => {
    walk(r.result.summary, 'summary', i + 1)
    walk(r.result.data, 'data', i + 1)
  })
  return out
}

/**
 * For each number in the answer: the source value it matches under the
 * grounding rule (two significant figures, percent <-> fraction), choosing the
 * closest one when several match, or null.
 */
export function groundingTrace(turn) {
  const src = sourceNumbers(turn)
  return numbersIn(turn.answer_md).map((v) => {
    let best = null, bestErr = Infinity
    for (const s of src) {
      for (const k of [1, 100, 0.01]) {
        if (sig2(s.value * k) !== sig2(v)) continue
        const err = Math.abs(s.value * k - v) / (Math.abs(v) || 1)
        if (err < bestErr) { bestErr = err; best = s }
      }
    }
    return { value: v, source: best }
  })
}
