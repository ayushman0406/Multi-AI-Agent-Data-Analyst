import { forwardRef, useImperativeHandle, useLayoutEffect, useRef, useState } from 'react'
import { ArrowUp, Square } from 'lucide-react'

const Composer = forwardRef(function Composer({ onSend, onStop, busy, disabled, placeholder, note }, ref) {
  const [value, setValue] = useState('')
  const ta = useRef(null)
  useImperativeHandle(ref, () => ({ focus: () => ta.current?.focus(), set: (v) => { setValue(v); ta.current?.focus() } }))
  useLayoutEffect(() => {
    const el = ta.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(200, el.scrollHeight) + 'px'
  }, [value])

  const send = async () => {
    const q = value.trim()
    if (!q || busy || disabled) return
    const res = await onSend(q)
    if (res?.ok !== false) setValue('')
  }
  return (
    <form className="composer" onSubmit={(e) => { e.preventDefault(); send() }}>
      <label htmlFor="composer-input" className="sr-only">Ask a question about this dataset</label>
      <textarea
        id="composer-input" ref={ta} rows={1} value={value} disabled={disabled}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send() }
        }}
        aria-describedby="composer-hint"
      />
      {busy ? (
        <button type="button" className="composer-btn is-stop" onClick={onStop} aria-label="Stop"><Square size={14} fill="currentColor" /></button>
      ) : (
        <button type="submit" className="composer-btn" disabled={!value.trim() || disabled} aria-label="Send question"><ArrowUp size={18} /></button>
      )}
      <p id="composer-hint" className="composer-hint">{note || <><kbd>Enter</kbd> to send · <kbd>Shift</kbd>+<kbd>Enter</kbd> for a new line · follow-ups can change the previous analysis</>}</p>
    </form>
  )
})
export default Composer
