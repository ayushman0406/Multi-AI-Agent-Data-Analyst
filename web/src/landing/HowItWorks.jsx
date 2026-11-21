import { useEffect, useMemo, useRef, useState } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { Check } from 'lucide-react'
import Split from './Split.jsx'
import ColumnCard from '../workspace/ColumnCard.jsx'
import DataTable from '../charts/DataTable.jsx'
import { demo, turn1 } from './data.js'
import { renderAnswer } from '../lib/answer.js'
import { prefersReduced } from './useLandingMotion.js'

function Json({ value }) {
  // tiny, safe highlighter: React text nodes only
  const inline = (o) => JSON.stringify(o).replace(/","/g, '", "').replace(/":/g, '": ').replace(/,\{/g, ', {')
  const text = '[\n' + value.map((s) => `  {\n    "tool": ${JSON.stringify(s.tool)},\n    "args": ${inline(s.args)},\n    "why": ${JSON.stringify(s.why)}\n  }`).join(',\n') + '\n]'
  const lines = text.split('\n')
  return (
    <pre className="json" tabIndex={0} aria-label="Plan as JSON">
      {lines.map((l, i) => {
        const m = l.match(/^(\s*)"([^"]+)":\s(.*)$/)
        return (
          <span key={i} className="json-line">
            {m ? <>{m[1]}<span className="json-k">"{m[2]}"</span>: <span className={/^"/.test(m[3]) ? 'json-s' : /^[{[]/.test(m[3]) ? 'json-o' : 'json-v'}>{m[3]}</span></> : l}
          </span>
        )
      })}
    </pre>
  )
}

const cols = Object.fromEntries(demo.profile.columns.map((c) => [c.name, c]))
const s1 = turn1.results[0]

const STAGES = [
  {
    key: 'understand', title: 'Understand',
    body: 'Every column is profiled in DuckDB: type, gaps, range, distribution, most common values. A model then writes what the dataset is, what each column means and which questions are worth asking. Without a model you still get the measurements, just no prose.',
    art: () => (
      <div className="art art-understand">
        <blockquote className="art-quote">“{demo.understanding.summary}”</blockquote>
        <ul className="cols art-cols">
          {['region', 'revenue', 'discount'].map((n) => <ColumnCard key={n} col={cols[n]} note={demo.understanding.column_notes[n]} rows={demo.profile.row_count} />)}
        </ul>
      </div>
    ),
  },
  {
    key: 'plan', title: 'Plan',
    body: 'For each question, a planner model chooses up to five calls from a fixed list of eleven analysis tools and says why. It cannot write code. Unknown tools and invalid arguments are dropped before anything runs.',
    art: () => (
      <div className="art">
        <p className="art-cap mono">planner output · “{turn1.question}”</p>
        <Json value={turn1.plan} />
      </div>
    ),
  },
  {
    key: 'run', title: 'Run',
    body: 'Each call compiles to parameterised SQL against your table. Column names are checked against the schema and quoted; values are bound, never pasted in. A tool returns rows, a chart spec and a few headline numbers.',
    art: () => (
      <div className="art">
        <p className="art-cap mono">group_aggregate · the SQL it runs, abridged</p>
        <pre className="sql">{`WITH g AS (\n  SELECT "region" AS grp,\n         SUM("revenue") AS val,\n         COUNT(*) AS n\n  FROM data\n  GROUP BY 1\n)\nSELECT grp, val, n FROM g\nORDER BY val DESC NULLS LAST, grp\nLIMIT 10`}</pre>
        <p className="art-cap mono">result · {s1.ms} ms</p>
        <DataTable rows={s1.result.data} caption="group_aggregate result" />
      </div>
    ),
  },
  {
    key: 'answer', title: 'Answer',
    body: 'A second model writes the reply from the question, the results and the conversation so far. It is told to use only numbers that appear in the results and to cite the step each one came from.',
    art: () => <AnswerArt checked={false} />,
  },
  {
    key: 'check', title: 'Check',
    body: 'Every number in the reply is compared with every number the tools returned. Matches are underlined. Anything that does not match is highlighted for you, not quietly removed.',
    art: () => <AnswerArt checked />,
  },
]

function AnswerArt({ checked }) {
  const html = useMemo(() => renderAnswer(turn1.answer_md, { ungrounded: checked ? turn1.ungrounded : null, question: turn1.question, steps: 2 }), [checked])
  return (
    <div className="art">
      <p className="art-cap mono">{checked ? 'after the grounding check' : 'answer model output'}</p>
      <div className="answer-md art-answer" dangerouslySetInnerHTML={{ __html: html }} />
      {checked && (
        <p className="ground is-ok"><Check size={14} strokeWidth={2.5} aria-hidden="true" /> <span><strong className="tnum">{turn1.grounded_count} of {turn1.total_numbers}</strong> numbers trace to a computed result</span></p>
      )}
    </div>
  )
}

export default function HowItWorks() {
  const [active, setActive] = useState(0)
  const [live, setLive] = useState(false)
  const root = useRef(null)
  const bar = useRef(null)

  useEffect(() => {
    if (prefersReduced()) return
    const mm = gsap.matchMedia()
    mm.add('(min-width: 901px)', () => {
      setLive(true)
      const arts = gsap.utils.toArray(root.current.querySelectorAll('.how-stage'))
      arts.forEach((el, i) => ScrollTrigger.create({ trigger: el, start: 'top 55%', end: 'bottom 55%', onToggle: (s) => s.isActive && setActive(i) }))
      gsap.fromTo(bar.current, { scaleY: 0 }, { scaleY: 1, ease: 'none', scrollTrigger: { trigger: root.current.querySelector('.how-arts'), start: 'top 55%', end: 'bottom 55%', scrub: true } })
      return () => setLive(false)
    })
    return () => mm.revert()
  }, [])

  return (
    <section className={`how${live ? ' is-live' : ''}`} id="how" ref={root} aria-labelledby="how-title">
      <div className="wrap how-grid">
        <div className="how-side">
          <p className="eyebrow">How it works</p>
          <Split text="Five stages, each one you can inspect." id="how-title" className="h2" />
          <ol className="how-nav">
            <span className="how-rail" aria-hidden="true"><span ref={bar} /></span>
            {STAGES.map((s, i) => (
              <li key={s.key} className={i === active ? 'is-active' : ''}>
                <span className="how-n mono">0{i + 1}</span>
                <div>
                  <h3>{s.title}</h3>
                  <p>{s.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
        <div className="how-arts">
          {STAGES.map((s, i) => (
            <div key={s.key} className={`how-stage${i === active ? ' is-active' : ''}`}>
              <div className="how-stage-text">
                <span className="how-n mono">0{i + 1}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
              {s.art()}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
