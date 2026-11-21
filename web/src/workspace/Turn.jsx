import { useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, CircleDashed, Undo2 } from 'lucide-react'
import Step from './Step.jsx'
import { renderAnswer } from '../lib/answer.js'
import { fmtMs } from '../lib/format.js'
import { phaseText } from './turns.js'

function Grounding({ turn }) {
  if (turn.status === 'checking' && turn.ungrounded === null) {
    return <p className="ground is-pending"><CircleDashed size={15} aria-hidden="true" /> Checking numbers against the tool results…</p>
  }
  if (turn.ungrounded === null || turn.total_numbers === null) return null
  const total = turn.total_numbers
  const ok = turn.grounded_count ?? total - turn.ungrounded.length
  if (!total) return <p className="ground is-none"><CheckCircle2 size={15} aria-hidden="true" /> No figures in this answer to check.</p>
  const clean = ok === total
  return (
    <p className={`ground ${clean ? 'is-ok' : 'is-warn'}`}>
      {clean ? <CheckCircle2 size={15} aria-hidden="true" /> : <AlertTriangle size={15} aria-hidden="true" />}
      <span><strong className="tnum">{ok} of {total}</strong> numbers trace to a computed result</span>
      {!clean && <span className="ground-hint">The highlighted {total - ok === 1 ? 'number does' : 'numbers do'} not appear in any tool output. Treat {total - ok === 1 ? 'it' : 'them'} as unverified.</span>}
    </p>
  )
}

/** Key-number `step` values are 1-based like the [n] references in the answer. */
const stepOf = (k, n) => (typeof k.step === 'number' ? Math.min(n, Math.max(1, k.step === 0 ? 1 : k.step)) : null)

export default function Turn({ turn, n, onAsk, disabled, canAsk = () => true, isLast }) {
  const [open, setOpen] = useState(() => new Set())
  const [flash, setFlash] = useState(null)
  const stepRefs = useRef([])
  const answerRef = useRef(null)
  const live = turn.status !== 'done' && turn.status !== 'error'

  const html = useMemo(
    () => renderAnswer(turn.answer_md, { ungrounded: turn.ungrounded, question: turn.question, steps: turn.steps.length }),
    [turn.answer_md, turn.ungrounded, turn.question, turn.steps.length],
  )

  const goto = (k) => {
    const i = k - 1
    if (!turn.steps[i]) return
    setOpen((s) => new Set(s).add(i))
    setFlash(i)
    requestAnimationFrame(() => {
      const el = stepRefs.current[i]
      el?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' })
      el?.querySelector('.step-row')?.focus({ preventScroll: true })
    })
  }
  useEffect(() => {
    if (flash === null) return
    const t = setTimeout(() => setFlash(null), 1400)
    return () => clearTimeout(t)
  }, [flash])

  const onAnswerClick = (e) => {
    const b = e.target.closest('button.ref')
    if (b) goto(Number(b.dataset.step))
  }

  const totalMs = turn.steps.reduce((a, s) => a + (s.ms || 0), 0)
  const toggle = (i) => setOpen((s) => { const nx = new Set(s); nx.has(i) ? nx.delete(i) : nx.add(i); return nx })

  return (
    <article className={`turn is-${turn.status}`} aria-labelledby={`${turn.id}-q`} aria-busy={live}>
      <header className="turn-head">
        <p className="turn-meta eyebrow">
          <span>Question {n}</span>
          {turn.recorded && <span className="tag-recorded">recorded</span>}
          {live && <span className="turn-phase">{phaseText(turn)}</span>}
        </p>
        <h2 className="turn-q" id={`${turn.id}-q`}>{turn.question}</h2>
      </header>

      <section className="plan" aria-label="Plan">
        <h3 className="plan-h">
          <span>Plan</span>
          {turn.steps.length > 0 && <span className="tnum">{turn.steps.length} {turn.steps.length === 1 ? 'step' : 'steps'}</span>}
          {totalMs > 0 && !live && <span className="tnum">{fmtMs(totalMs)} in DuckDB</span>}
        </h3>
        {turn.status === 'planning' ? (
          <p className="plan-wait"><span className="spinner" aria-hidden="true" /> Choosing from the tool list…</p>
        ) : turn.steps.length ? (
          <ol className="steps">
            {turn.steps.map((s, i) => (
              <Step key={i} ref={(el) => (stepRefs.current[i] = el)} step={s} n={i + 1} turnId={turn.id}
                open={open.has(i)} flash={flash === i} onToggle={() => toggle(i)} />
            ))}
          </ol>
        ) : (
          <p className="plan-wait">No tools were needed for this question.</p>
        )}
      </section>

      {turn.answer_md ? (
        <section className="answer" aria-label="Answer">
          {/* eslint-disable-next-line react/no-danger -- sanitised by DOMPurify in renderAnswer */}
          <div className="answer-md" ref={answerRef} onClick={onAnswerClick} dangerouslySetInnerHTML={{ __html: html }} />
          {turn.key_numbers?.length > 0 && (
            <ul className="keys">
              {turn.key_numbers.map((k, i) => {
                const s = stepOf(k, turn.steps.length)
                return (
                  <li key={i} className="key">
                    <span className="key-value">{String(k.value)}</span>
                    <span className="key-label">{k.label}</span>
                    {s && <button type="button" className="key-step mono" onClick={() => goto(s)}>from step {s}</button>}
                  </li>
                )
              })}
            </ul>
          )}
          <Grounding turn={turn} />
        </section>
      ) : turn.status === 'answering' ? (
        <p className="plan-wait"><span className="spinner" aria-hidden="true" /> Writing the answer using only these results…</p>
      ) : null}

      {turn.status === 'error' && (
        <p className="turn-error" role="alert"><AlertTriangle size={15} aria-hidden="true" /> {turn.error}</p>
      )}

      {turn.status === 'done' && turn.follow_ups?.length > 0 && isLast && (
        <div className="follow">
          <h3 className="follow-h"><Undo2 size={14} aria-hidden="true" style={{ transform: 'scaleX(-1)' }} /> Follow up — this changes the analysis above</h3>
          <ul className="chips">
            {turn.follow_ups.map((q) => (
              <li key={q}><button type="button" className="chip" disabled={disabled || !canAsk(q)} title={canAsk(q) ? undefined : 'Not in this recording'} onClick={() => onAsk(q)}>{q}</button></li>
            ))}
          </ul>
        </div>
      )}
    </article>
  )
}
