import { useEffect, useRef, useState } from 'react'
import { X } from 'lucide-react'
import { api, friendlyError } from '../lib/api.js'

export default function SettingsDrawer({ open, onClose, onSaved, health }) {
  const [form, setForm] = useState({ api_key: '', base_url: '', model: '' })
  const [current, setCurrent] = useState(null)
  const [state, setState] = useState({ saving: false, error: null, saved: false })
  const panel = useRef(null)
  const lastFocus = useRef(null)

  useEffect(() => {
    if (!open) return
    lastFocus.current = document.activeElement
    setState({ saving: false, error: null, saved: false })
    api.getSettings().then((s) => { setCurrent(s); setForm({ api_key: '', base_url: s.base_url || '', model: s.model || '' }) })
      .catch((e) => setState((x) => ({ ...x, error: friendlyError(e) })))
    const t = setTimeout(() => panel.current?.querySelector('input')?.focus(), 30)
    return () => { clearTimeout(t); lastFocus.current?.focus?.() }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'Tab' && panel.current) {
        const f = [...panel.current.querySelectorAll('button, input, a[href]')].filter((el) => !el.disabled)
        if (!f.length) return
        if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f.at(-1).focus() }
        else if (!e.shiftKey && document.activeElement === f.at(-1)) { e.preventDefault(); f[0].focus() }
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  const save = async (e) => {
    e.preventDefault()
    setState({ saving: true, error: null, saved: false })
    const body = {}
    if (form.api_key.trim()) body.api_key = form.api_key.trim()
    if (form.base_url.trim()) body.base_url = form.base_url.trim()
    if (form.model.trim()) body.model = form.model.trim()
    try {
      const s = await api.putSettings(body)
      setCurrent(s && typeof s === 'object' && 'has_key' in s ? s : { ...current, ...body, has_key: current?.has_key || !!body.api_key })
      setForm((f) => ({ ...f, api_key: '' }))
      setState({ saving: false, error: null, saved: true })
      onSaved?.()
    } catch (err) {
      setState({ saving: false, error: friendlyError(err), saved: false })
    }
  }
  return (
    <div className="drawer-wrap">
      <div className="drawer-scrim" onClick={onClose} aria-hidden="true" />
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="settings-title" ref={panel}>
        <div className="drawer-head">
          <h2 id="settings-title">Model settings</h2>
          <button type="button" className="btn btn-quiet icon-btn" onClick={onClose} aria-label="Close settings"><X size={18} /></button>
        </div>
        <p className="drawer-lede">Any OpenAI-compatible endpoint works: Groq, OpenAI, OpenRouter, Together, a local Ollama or vLLM server. These settings apply to this server process until it restarts.</p>
        <form onSubmit={save} className="form">
          <label className="field">
            <span className="field-label">API key</span>
            <input type="password" autoComplete="off" spellCheck="false" value={form.api_key}
              placeholder={current?.has_key ? 'A key is set — leave empty to keep it' : 'sk-… or gsk_…'}
              onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
            <span className="field-help">Sent to your server once. It is never sent back to the browser.</span>
          </label>
          <label className="field">
            <span className="field-label">Base URL</span>
            <input type="url" spellCheck="false" value={form.base_url} placeholder="https://api.groq.com/openai/v1"
              onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
          </label>
          <label className="field">
            <span className="field-label">Model</span>
            <input type="text" spellCheck="false" value={form.model} placeholder="openai/gpt-oss-120b"
              onChange={(e) => setForm({ ...form, model: e.target.value })} />
            <span className="field-help">Needs JSON mode. Planning and answering both use this model.</span>
          </label>
          <div className="drawer-status" aria-live="polite">
            {state.error && <p className="form-error">{state.error}</p>}
            {state.saved && <p className="form-ok">Saved. {health?.llm?.configured ? `Using ${health.llm.model}.` : ''}</p>}
          </div>
          <div className="drawer-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Close</button>
            <button type="submit" className="btn btn-primary" disabled={state.saving}>{state.saving ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
        <div className="drawer-foot">
          <h3 className="eyebrow">Without a key</h3>
          <p>The app still works offline. Plans come from keyword rules, the same tools run, and the answer is a plain table of their results. Nothing is written by a model, so nothing can be made up.</p>
        </div>
      </aside>
    </div>
  )
}
