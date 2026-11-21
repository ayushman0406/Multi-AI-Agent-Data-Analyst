import { useEffect, useMemo, useRef, useState } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { AlertTriangle, Check, X } from 'lucide-react'
import Split from './Split.jsx'
import { turn2, groundingTrace } from './data.js'
import { renderAnswer } from '../lib/answer.js'
import { fmtNum } from '../lib/format.js'
import { prefersReduced } from './useLandingMotion.js'

export default function GroundingScrub() {
  const trace = useMemo(() => groundingTrace(turn2), [])
  const n = trace.length
  const [idx, setIdx] = useState(n) // number of numbers checked; final state by default
  const root = useRef(null)
  const pin = useRef(null)
  const answer = useRef(null)
  const html = useMemo(() => renderAnswer(turn2.answer_md, { ungrounded: turn2.ungrounded, question: turn2.question, steps: 2 }), [])

  useEffect(() => {
    if (prefersReduced()) return
    const mm = gsap.matchMedia()
    mm.add('(min-width: 901px) and (min-height: 620px)', () => {
      setIdx(0)
      const st = ScrollTrigger.create({
        trigger: pin.current, start: 'top top', end: `+=${n * 38 + 40}%`, pin: true, scrub: true,
        onUpdate: (s) => setIdx(Math.min(n, Math.floor(s.progress * (n + 0.999)))),
      })
      return () => { st.kill(); setIdx(n) }
    })
    return () => mm.revert()
  }, [n])

  useEffect(() => {
    const spans = answer.current?.querySelectorAll('.num') || []
    spans.forEach((s, i) => {
      s.classList.toggle('is-checked', i < idx)
      s.classList.toggle('is-current', i === idx - 1 && idx < n)
    })
  }, [idx, n, html])

  const checked = trace.slice(0, idx)
  const ok = checked.filter((t) => t.source).length
  const done = idx >= n
  const current = idx > 0 ? trace[idx - 1] : null
  const example = trace.find((t) => t.source && t.source.value !== t.value)

  return (
    <section className="ground-sec" id="grounding" ref={root} aria-labelledby="ground-title">
      <div className="ground-pin" ref={pin}>
        <div className="wrap ground-grid">
          <div className="ground-left">
            <p className="eyebrow">The grounding check</p>
            <Split text="Every figure is looked up in the results." id="ground-title" className="h2" />
            <p className="lede">This is the second answer from the example session (real tool results, hand-written answer with one unsupported figure planted on purpose). The check pulls each number out of the text and searches everything the tools returned for it.</p>
            <div className="ground-answer answer-md" ref={answer} dangerouslySetInnerHTML={{ __html: html }} />
            <p className={`ground-count${done ? ' is-done' : ''}`} aria-live="polite">
              {done ? (
                <><AlertTriangle size={15} aria-hidden="true" /> <span><strong className="tnum">{turn2.grounded_count} of {turn2.total_numbers}</strong> numbers trace to a computed result. “12%” is not in any tool output, so it is flagged.</span></>
              ) : (
                <span className="mono tnum">checked {idx} of {n}</span>
              )}
            </p>
          </div>
          <div className="ground-right">
            <p className="art-cap mono">numbers in the reply → where they were found</p>
            <ol className="lookup">
              {trace.map((t, i) => (
                <li key={i} className={`${i < idx ? 'is-checked' : ''}${current === t ? ' is-current' : ''}${t.source ? '' : ' is-miss'}`}>
                  <span className="lookup-num mono tnum">{fmtNum(t.value)}</span>
                  <span className="lookup-arrow" aria-hidden="true">→</span>
                  <span className="lookup-src mono">
                    {i < idx ? (t.source ? <>step {t.source.step} · {t.source.path} = <b className="tnum">{fmtNum(t.source.value)}</b></> : 'no match in any result') : '…'}
                  </span>
                  <span className="lookup-ico" aria-hidden="true">{i < idx ? (t.source ? <Check size={13} strokeWidth={2.5} /> : <X size={13} strokeWidth={2.5} />) : null}</span>
                </li>
              ))}
            </ol>
            <ul className="rules">
              {example && <li>Numbers match if they agree to two significant figures, so <span className="mono">{fmtNum(example.value)}</span> matches <span className="mono">{example.source.value}</span>.</li>}
              <li>A percentage matches its fraction, so <span className="mono">25%</span> would match <span className="mono">0.25</span>.</li>
              <li>Small whole numbers (0–10), years, and numbers from your own question are skipped.</li>
            </ul>
            <span className="sr-only">{ok} of {checked.length} checked so far.</span>
          </div>
        </div>
      </div>
    </section>
  )
}
