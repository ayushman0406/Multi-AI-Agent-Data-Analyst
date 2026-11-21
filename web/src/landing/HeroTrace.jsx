import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, RotateCcw } from 'lucide-react'
import { demo, turn1 } from './data.js'
import { renderAnswer } from '../lib/answer.js'
import { argSummary } from '../workspace/turns.js'
import { fmtInt, fmtTick } from '../lib/format.js'

// phases: 0 typing · 1 step1 running · 2 step1 done · 3 step2 running · 4 step2 done
//         5 answer · 6 numbers checked · 7 badge
const FINAL = 7
const reduced = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

export default function HeroTrace() {
  const q = turn1.question
  const [chars, setChars] = useState(0)
  const [phase, setPhase] = useState(0)
  const [run, setRun] = useState(0)
  const timers = useRef([])

  useEffect(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
    if (reduced()) { setChars(q.length); setPhase(FINAL); return }
    setChars(0); setPhase(0)
    const at = (ms, fn) => timers.current.push(setTimeout(fn, ms))
    for (let i = 1; i <= q.length; i++) at(500 + i * 26, () => setChars(i))
    const t0 = 500 + q.length * 26 + 350
    ;[0, 650, 1150, 1750, 2350, 3600, 4300].forEach((d, i) => at(t0 + d, () => setPhase(i + 1)))
    return () => timers.current.forEach(clearTimeout)
  }, [run, q])

  const [s1, s2] = turn1.results
  const bars = s1.result.data
  const max = Math.max(...bars.map((b) => b.sum_revenue))
  const html = useMemo(() => renderAnswer(turn1.answer_md, { ungrounded: phase >= 6 ? turn1.ungrounded : null, question: q, steps: 2 }), [phase, q])
  const stepState = (i) => (phase >= (i === 0 ? 2 : 4) ? 'done' : phase >= (i === 0 ? 1 : 3) ? 'running' : 'pending')

  return (
    <figure className="trace" aria-label="Example: a question answered by the analyst, from a recorded session">
      <div className="trace-bar">
        <span className="mono">{demo.dataset.name}</span>
        <span className="mono tnum">{fmtInt(demo.dataset.rows)} rows · {demo.dataset.columns} cols</span>
        <span className="trace-rec">recorded</span>
      </div>

      <div className="trace-body">
        <p className="trace-q">
          <span className="sr-only">{q}</span>
          <span aria-hidden="true">{q.slice(0, chars)}<span className={`caret${phase > 0 ? ' is-off' : ''}`} /></span>
        </p>

        <ol className="trace-steps" aria-label="Plan">
          {[s1, s2].map((s, i) => {
            const st = stepState(i)
            return (
              <li key={i} className={`trace-step is-${st}${phase >= (i === 0 ? 1 : 3) ? ' is-in' : ''}`}>
                <span className="trace-n mono">{i + 1}</span>
                <span className="trace-ico" aria-hidden="true">{st === 'done' ? <Check size={11} strokeWidth={3} /> : st === 'running' ? <span className="spinner" /> : null}</span>
                <span className="trace-tool mono">{s.tool}</span>
                <span className="trace-args mono">{argSummary(s.tool, s.args)}</span>
                <span className="trace-ms mono tnum">{st === 'done' ? `${s.ms} ms` : ''}</span>
              </li>
            )
          })}
        </ol>

        <div className={`trace-result${phase >= 2 ? ' is-in' : ''}`} aria-hidden={phase < 2}>
          <p className="trace-label mono">step 1 · sum of revenue by region</p>
          <ul className="trace-bars">
            {bars.map((b) => (
              <li key={b.region}>
                <span>{b.region}</span>
                <span className="trace-track"><span style={{ width: phase >= 2 ? `${(b.sum_revenue / max) * 100}%` : '0%' }} /></span>
                <span className="mono tnum">{fmtTick(b.sum_revenue, max)}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className={`trace-answer answer-md${phase >= 5 ? ' is-in' : ''}${phase >= 6 ? ' is-checked' : ''}`} aria-hidden={phase < 5} dangerouslySetInnerHTML={{ __html: html }} />

        <div className="trace-foot">
          <p className={`trace-badge${phase >= 7 ? ' is-in' : ''}`} aria-hidden={phase < 7}>
            <Check size={13} strokeWidth={2.5} aria-hidden="true" />
            <span><strong className="tnum">{turn1.grounded_count} of {turn1.total_numbers}</strong> numbers trace to a computed result</span>
          </p>
          <button type="button" className="trace-replay" onClick={() => setRun((r) => r + 1)} aria-label="Replay the example">
            <RotateCcw size={13} aria-hidden="true" /> Replay
          </button>
        </div>
      </div>
      <p className="trace-time mono" aria-hidden="true">{s2 && `${s1.ms + s2.ms} ms in DuckDB`}</p>
    </figure>
  )
}
