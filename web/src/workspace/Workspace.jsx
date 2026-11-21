import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Download, PanelLeftClose, PanelLeftOpen, Plus, Settings2, WifiOff, Info, PlayCircle } from 'lucide-react'
import { api } from '../lib/api.js'
import { useSession } from './useSession.js'
import StartPanel from './StartPanel.jsx'
import Brief from './Brief.jsx'
import Turn from './Turn.jsx'
import Composer from './Composer.jsx'
import SettingsDrawer from './SettingsDrawer.jsx'
import { phaseText } from './turns.js'
import { recordedReport } from './report.js'
import './workspace.css'

function useHealth() {
  const [health, setHealth] = useState({ state: 'checking' })
  const check = useCallback(async () => {
    const ac = new AbortController()
    const t = setTimeout(() => ac.abort(), 4000)
    try {
      const h = await api.health(ac.signal)
      setHealth({ state: 'up', ...h })
    } catch {
      setHealth({ state: 'down' })
    } finally { clearTimeout(t) }
  }, [])
  useEffect(() => { check() }, [check])
  return [health, check]
}

function useMedia(q) {
  const [m, setM] = useState(() => typeof matchMedia !== 'undefined' && matchMedia(q).matches)
  useEffect(() => {
    const mq = matchMedia(q)
    const on = () => setM(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [q])
  return m
}

export default function Workspace() {
  const [health, recheck] = useHealth()
  const s = useSession()
  const [params, setParams] = useSearchParams()
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [railOpen, setRailOpen] = useState(true)
  const [notice, setNotice] = useState(null)
  const composer = useRef(null)
  const narrow = useMedia('(max-width: 900px)')
  const serverUp = health.state === 'up'
  const { session, turns } = s
  const recorded = session?.mode === 'recorded'

  useEffect(() => { document.title = session ? `${session.understanding?.title || session.dataset?.name} — Analyst` : 'Workspace — Analyst' }, [session])

  // ?demo=1 opens the recording; ?sample=<id> opens a sample directly
  const booted = useRef(false)
  useEffect(() => {
    if (booted.current || health.state === 'checking') return
    booted.current = true
    if (params.get('demo') !== null) s.openRecording({ autoplay: params.get('demo') !== 'still' })
    else if (params.get('sample') && serverUp) s.open({ sampleId: params.get('sample'), label: params.get('sample') })
  }, [health.state, params, serverUp, s])

  // bring a new question to the top of the view once; don't fight the reader while it streams
  const last = turns.at(-1)
  const lastId = last?.id
  useEffect(() => {
    if (!lastId) return
    const el = document.getElementById(`${lastId}-q`)?.closest('article')
    el?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' })
  }, [lastId])

  const ask = async (q) => {
    setNotice(null)
    const res = await s.ask(q)
    if (res?.reason === 'recorded') {
      setNotice('This is a recording, so only the questions it contains can be replayed. Start the server to ask your own.')
      return { ok: false }
    }
    return res
  }

  const exportReport = () => {
    if (!session) return
    if (recorded) {
      const blob = new Blob([recordedReport(session, turns)], { type: 'text/markdown' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = 'recorded-example-report.md'
      a.click()
      setTimeout(() => URL.revokeObjectURL(a.href), 1000)
    } else {
      const a = document.createElement('a')
      a.href = api.reportUrl(session.id)
      a.download = `${(session.dataset?.name || 'analysis').replace(/\.[^.]+$/, '')}-report.md`
      a.click()
    }
  }

  const newDataset = () => {
    s.reset()
    setNotice(null)
    if (params.toString()) setParams({}, { replace: true })
  }

  const llm = health.llm
  const offline = serverUp && llm && !llm.configured
  const recordedQs = recorded ? new Set((session.recording?.turns || []).map((t) => t.question)) : null
  const asked = new Set(turns.map((t) => t.question))
  const canAsk = (q) => !recorded || (recordedQs.has(q) && !asked.has(q))
  const nextRecorded = recorded ? (session.recording?.turns || []).find((t) => !asked.has(t.question)) : null

  return (
    <div className="ws">
      <a href="#main" className="skip-link">Skip to conversation</a>
      <header className="ws-bar">
        <Link to="/" className="wordmark" aria-label="Analyst, back to the overview">Analyst</Link>
        {session && (
          <p className="ws-crumb">
            <span className="ws-crumb-sep" aria-hidden="true">/</span>
            <span className="mono">{session.dataset?.name}</span>
          </p>
        )}
        <div className="ws-bar-right">
          <span className={`model-pill${recorded ? ' is-rec' : offline || !serverUp ? ' is-off' : ''}`} title={llm?.base_url_host || ''}>
            {recorded ? 'recorded' : health.state === 'checking' ? 'connecting…' : !serverUp ? 'server offline' : llm?.configured ? llm.model : 'offline mode'}
          </span>
          {session && (
            <>
              <button type="button" className="btn btn-quiet" onClick={exportReport} disabled={!turns.some((t) => t.status === 'done')}>
                <Download aria-hidden="true" /> <span className="hide-sm">Export</span><span className="sr-only"> report as Markdown</span>
              </button>
              <button type="button" className="btn btn-quiet" onClick={newDataset}><Plus aria-hidden="true" /> <span className="hide-sm">New dataset</span><span className="sr-only">Start over with a new dataset</span></button>
            </>
          )}
          <button type="button" className="btn btn-quiet" onClick={() => setSettingsOpen(true)} disabled={!serverUp}>
            <Settings2 aria-hidden="true" /> <span className="hide-sm">Model</span><span className="sr-only"> settings</span>
          </button>
        </div>
      </header>

      {recorded ? (
        <div className="banner is-rec" role="note">
          <PlayCircle size={16} aria-hidden="true" />
          <p><strong>Recorded example.</strong> {session.recording?.recorded_note || 'Replayed from a saved session; nothing here is computed live.'} {session.recording?.source === 'bundled' ? 'Loaded from a copy bundled with the page.' : ''}</p>
        </div>
      ) : health.state === 'down' ? (
        <div className="banner is-warn" role="status">
          <WifiOff size={16} aria-hidden="true" />
          <p><strong>The server isn't reachable.</strong> Start the backend on port 8000 to analyse your own files. Meanwhile you can <button type="button" className="linklike" onClick={() => s.openRecording()}>watch the recorded example</button>. <button type="button" className="linklike" onClick={recheck}>Try again</button></p>
        </div>
      ) : offline ? (
        <div className="banner is-info" role="status">
          <Info size={16} aria-hidden="true" />
          <p><strong>No model configured — offline mode.</strong> You can still load data and ask questions: plans come from keyword rules, the same audited tools run, and answers are plain tables of the results. <button type="button" className="linklike" onClick={() => setSettingsOpen(true)}>Add an API key</button> for written answers.</p>
        </div>
      ) : null}

      {!session ? (
        <main id="main" className="ws-start">
          <StartPanel serverUp={serverUp} onOpen={s.open} onRecording={() => s.openRecording()} loading={s.loading} error={s.loadError} />
        </main>
      ) : (
        <div className={`ws-grid${railOpen ? '' : ' is-collapsed'}`}>
          <aside className="rail" aria-label="Dataset">
            {!narrow && (
              <button type="button" className="btn btn-quiet icon-btn rail-toggle" onClick={() => setRailOpen((v) => !v)} aria-expanded={railOpen} aria-label={railOpen ? 'Collapse dataset panel' : 'Expand dataset panel'}>
                {railOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
              </button>
            )}
            {(railOpen || narrow) && <Brief session={session} onAsk={ask} disabled={s.busy} canAsk={canAsk} compact={narrow} />}
          </aside>

          <main id="main" className="thread-col">
            <div className="thread">
              {turns.length === 0 && (
                <div className="thread-empty">
                  <p className="eyebrow">Conversation</p>
                  <h2>Ask a question about {session.understanding?.title ? <em>{session.understanding.title.toLowerCase()}</em> : 'this data'}.</h2>
                  <p>Each answer shows the plan it ran, the result of every step, and which numbers in the reply came from those results.</p>
                </div>
              )}
              {turns.map((t, i) => (
                <Turn key={t.id} turn={t} n={i + 1} onAsk={ask} disabled={s.busy} canAsk={canAsk} isLast={i === turns.length - 1} />
              ))}
              {recorded && nextRecorded && last?.status === 'done' && !last.follow_ups?.includes(nextRecorded.question) && (
                <div className="follow">
                  <h3 className="follow-h">Next in this recording</h3>
                  <ul className="chips"><li><button type="button" className="chip" onClick={() => ask(nextRecorded.question)}>{nextRecorded.question}</button></li></ul>
                </div>
              )}
            </div>
            <div className="sr-only" aria-live="polite" aria-atomic="true">
              {last ? `Question ${turns.length}: ${phaseText(last)}${last.status === 'done' && last.total_numbers ? `. ${last.grounded_count} of ${last.total_numbers} numbers trace to a computed result.` : ''}` : ''}
            </div>
            <div className="composer-dock">
              {notice && <p className="composer-notice" role="status">{notice}</p>}
              <Composer
                ref={composer}
                onSend={ask}
                onStop={s.stop}
                busy={s.busy}
                disabled={recorded}
                placeholder={recorded ? 'Recorded example — pick one of the suggested questions to replay it' : 'Ask about this dataset, or change the last analysis…'}
                note={recorded ? <>Replays only. {recordedQs?.size} questions are in this recording.</> : undefined}
              />
            </div>
          </main>
        </div>
      )}

      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} onSaved={recheck} health={health} />
    </div>
  )
}
