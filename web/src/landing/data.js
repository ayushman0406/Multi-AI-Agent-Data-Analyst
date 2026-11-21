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

/** For each number in the answer: the first source it matches, or null. */
export function groundingTrace(turn) {
  const src = sourceNumbers(turn)
  return numbersIn(turn.answer_md).map((v) => {
    const hit = src.find((s) => sig2(s.value) === sig2(v) || sig2(s.value * 100) === sig2(v) || sig2(s.value / 100) === sig2(v))
    return { value: v, source: hit || null }
  })
}
