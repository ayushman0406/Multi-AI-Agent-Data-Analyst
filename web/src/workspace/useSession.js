import { useCallback, useEffect, useRef, useState } from 'react'
import { api, friendlyError } from '../lib/api.js'
import { applyEvent, emptyTurn, norm, replayEvents, turnFromStored } from './turns.js'

const reduced = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches
const sleep = (ms, signal) => new Promise((res, rej) => {
  const t = setTimeout(res, ms)
  signal?.addEventListener('abort', () => { clearTimeout(t); rej(new DOMException('Aborted', 'AbortError')) }, { once: true })
})

async function loadRecording() {
  try {
    const d = await api.demo()
    if (d && d.profile) return { ...d, source: 'server' }
  } catch { /* fall through to bundled copy */ }
  const mod = await import('../demo/retail_demo.json')
  return { ...mod.default, source: 'bundled' }
}

/**
 * session: null | {
 *   mode: 'live'|'recorded', id, dataset, profile, understanding,
 *   understandStatus: 'streaming'|'done'|'error', understandError, recording?
 * }
 */
export function useSession() {
  const [session, setSession] = useState(null)
  const [turns, setTurns] = useState([])
  const [busy, setBusy] = useState(false)
  const [loadError, setLoadError] = useState(null)
  const [loading, setLoading] = useState(null) // label of what is loading
  const abortRef = useRef(null)

  const updateTurn = (id, fn) => setTurns((ts) => ts.map((t) => (t.id === id ? fn(t) : t)))

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setSession(null); setTurns([]); setBusy(false); setLoadError(null); setLoading(null)
  }, [])

  const streamUnderstanding = useCallback(async (id, signal) => {
    try {
      await api.understand(id, ({ event, data }) => {
        if (event === 'profile') setSession((s) => s && s.id === id ? { ...s, profile: data?.profile || data } : s)
        else if (event === 'understanding') setSession((s) => s && s.id === id ? { ...s, understanding: data?.understanding || data } : s)
        else if (event === 'error') setSession((s) => s && s.id === id ? { ...s, understandStatus: 'error', understandError: data?.message || data?.detail || String(data) } : s)
        else if (event === 'done') setSession((s) => s && s.id === id ? { ...s, understandStatus: s.understandStatus === 'error' ? 'error' : 'done' } : s)
      }, signal)
      setSession((s) => s && s.id === id && s.understandStatus === 'streaming' ? { ...s, understandStatus: 'done' } : s)
    } catch (err) {
      if (err?.name === 'AbortError') return
      setSession((s) => s && s.id === id ? { ...s, understandStatus: 'error', understandError: friendlyError(err) } : s)
    }
  }, [])

  const open = useCallback(async ({ file, sampleId, label }) => {
    abortRef.current?.abort()
    const ac = new AbortController()
    abortRef.current = ac
    setLoadError(null); setTurns([]); setLoading(label || file?.name || sampleId)
    try {
      const res = await api.createSession({ file, sampleId })
      const id = res.session_id
      setSession({ mode: 'live', id, dataset: res.dataset, profile: res.profile, understanding: res.understanding || null, understandStatus: 'streaming' })
      setLoading(null)
      streamUnderstanding(id, ac.signal)
    } catch (err) {
      setLoading(null)
      setLoadError(friendlyError(err))
    }
  }, [streamUnderstanding])

  const openRecording = useCallback(async ({ autoplay = true } = {}) => {
    abortRef.current?.abort()
    setLoadError(null); setTurns([]); setLoading('Recorded example')
    const rec = await loadRecording()
    setLoading(null)
    setSession({
      mode: 'recorded', id: rec.session_id || 'recorded', dataset: rec.dataset, profile: rec.profile,
      understanding: rec.understanding, understandStatus: 'done', recording: rec,
    })
    if (autoplay && rec.turns?.[0]) replay(rec, rec.turns[0])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function replay(rec, stored) {
    const ac = new AbortController()
    abortRef.current = ac
    const turn = emptyTurn(stored.question, { recorded: true })
    setTurns((ts) => [...ts, turn])
    setBusy(true)
    try {
      if (reduced()) {
        updateTurn(turn.id, () => ({ ...turnFromStored(stored), id: turn.id, recorded: true }))
      } else {
        for (const ev of replayEvents(stored)) {
          await sleep(ev.wait, ac.signal)
          updateTurn(turn.id, (t) => applyEvent(t, ev))
        }
      }
    } catch (err) {
      if (err?.name !== 'AbortError') updateTurn(turn.id, (t) => ({ ...t, status: 'error', error: friendlyError(err) }))
      else updateTurn(turn.id, () => ({ ...turnFromStored(stored), id: turn.id, recorded: true }))
    } finally {
      setBusy(false)
    }
  }

  const ask = useCallback(async (question) => {
    const q = question.trim()
    if (!q || busy || !session) return { ok: false }
    if (session.mode === 'recorded') {
      const rec = session.recording
      const stored = rec.turns?.find((t) => norm(t.question) === norm(q))
      if (!stored) return { ok: false, reason: 'recorded' }
      replay(rec, stored)
      return { ok: true }
    }
    const ac = new AbortController()
    abortRef.current = ac
    const turn = emptyTurn(q)
    setTurns((ts) => [...ts, turn])
    setBusy(true)
    let finished = false
    try {
      await api.ask(session.id, q, (ev) => {
        if (ev.event === 'done' || ev.event === 'error') finished = true
        updateTurn(turn.id, (t) => applyEvent(t, ev))
      }, ac.signal)
      if (!finished) updateTurn(turn.id, (t) => (t.status === 'done' ? t : { ...t, status: 'error', error: 'The stream ended before the answer was complete.' }))
    } catch (err) {
      updateTurn(turn.id, (t) => ({ ...t, status: 'error', error: friendlyError(err) }))
    } finally {
      setBusy(false)
    }
    return { ok: true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busy, session])

  const stop = useCallback(() => abortRef.current?.abort(), [])

  useEffect(() => () => abortRef.current?.abort(), [])

  return { session, turns, busy, loading, loadError, open, openRecording, ask, stop, reset, setLoadError }
}
