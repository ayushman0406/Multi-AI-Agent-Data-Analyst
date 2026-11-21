import { forwardRef } from 'react'
import { Check, ChevronRight, X } from 'lucide-react'
import Chart from '../charts/Chart.jsx'
import { fmtMs, fmtNum, humanize } from '../lib/format.js'
import { argSummary } from './turns.js'

function StatusIcon({ status }) {
  if (status === 'running') return <span className="step-status is-running" aria-label="running"><span className="spinner" /></span>
  if (status === 'done') return <span className="step-status is-done" aria-label="done"><Check size={13} strokeWidth={2.5} /></span>
  if (status === 'error') return <span className="step-status is-error" aria-label="failed"><X size={13} strokeWidth={2.5} /></span>
  return <span className="step-status is-pending" aria-label="waiting" />
}

function Args({ args }) {
  const entries = Object.entries(args || {}).filter(([, v]) => v !== null && v !== undefined)
  if (!entries.length) return <p className="step-none">No arguments.</p>
  return (
    <dl className="step-args">
      {entries.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{k === 'filters' && Array.isArray(v) && v.length === 0
            ? <span className="step-none">none</span>
            : k === 'filters' && Array.isArray(v)
            ? v.map((f, i) => <code key={i} className="filter">{f.column} {f.op} {JSON.stringify(f.value)}</code>)
            : <code>{typeof v === 'string' ? v : JSON.stringify(v)}</code>}</dd>
        </div>
      ))}
    </dl>
  )
}

const Step = forwardRef(function Step({ step, n, open, onToggle, flash, turnId }, ref) {
  const id = `${turnId}-step-${n}`
  const summary = step.result?.summary
  return (
    <li ref={ref} className={`step is-${step.status}${open ? ' is-open' : ''}${flash ? ' is-flash' : ''}`} id={id}>
      <button type="button" className="step-row" aria-expanded={open} aria-controls={`${id}-body`} onClick={onToggle}>
        <span className="step-n tnum" aria-hidden="true">{n}</span>
        <StatusIcon status={step.status} />
        <span className="step-main">
          <span className="step-tool">{step.tool}</span>
          <span className="step-sum">{argSummary(step.tool, step.args)}</span>
        </span>
        <span className="step-ms tnum">{step.status === 'done' || step.status === 'error' ? fmtMs(step.ms) : step.status === 'running' ? 'running' : ''}</span>
        <ChevronRight className="step-chev" size={16} aria-hidden="true" />
        <span className="sr-only">Step {n}, {step.status}</span>
      </button>
      {open && (
        <div className="step-body" id={`${id}-body`}>
          {step.why && <p className="step-why">{step.why}</p>}
          <div className="step-grid">
            <div>
              <h4 className="step-h">Arguments</h4>
              <Args args={step.args} />
            </div>
            {summary && Object.keys(summary).length > 0 && (
              <div>
                <h4 className="step-h">Headline numbers</h4>
                <dl className="step-summary tnum">
                  {Object.entries(summary).map(([k, v]) => (
                    <div key={k}><dt>{humanize(k)}</dt><dd>{typeof v === 'number' ? fmtNum(v) : String(v)}</dd></div>
                  ))}
                </dl>
              </div>
            )}
          </div>
          {step.status === 'error' && <p className="step-error" role="alert">{String(step.error)}</p>}
          {step.result && (
            <div className="step-chart">
              <Chart result={step.result} title={step.result.title} />
            </div>
          )}
          {(step.result || step.error) && (
            <details className="step-raw">
              <summary>Raw result JSON</summary>
              <pre>{JSON.stringify(step.result || { error: step.error }, null, 2)}</pre>
            </details>
          )}
          {step.status === 'pending' && <p className="step-none">Waiting to run.</p>}
          {step.status === 'running' && <p className="step-none">Running in DuckDB…</p>}
        </div>
      )}
    </li>
  )
})

export default Step
