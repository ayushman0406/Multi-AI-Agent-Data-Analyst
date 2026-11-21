// Minimal Server-Sent Events reader over fetch + ReadableStream.
// EventSource cannot POST, so both the GET /understand and the POST /ask
// streams go through this one parser.

export class HttpError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

/** Parse one SSE block ("event: x\ndata: {...}") into {event, data}. */
export function parseBlock(block) {
  let event = 'message'
  const data = []
  for (const raw of block.split('\n')) {
    const line = raw.endsWith('\r') ? raw.slice(0, -1) : raw
    if (!line || line.startsWith(':')) continue
    const i = line.indexOf(':')
    const field = i === -1 ? line : line.slice(0, i)
    let value = i === -1 ? '' : line.slice(i + 1)
    if (value.startsWith(' ')) value = value.slice(1)
    if (field === 'event') event = value
    else if (field === 'data') data.push(value)
  }
  if (!data.length && event === 'message') return null
  const text = data.join('\n')
  let parsed = text
  if (text) {
    try { parsed = JSON.parse(text) } catch { /* keep as string */ }
  } else parsed = null
  return { event, data: parsed }
}

/**
 * Stream SSE events from `url`. Calls onEvent({event, data}) for each one.
 * Resolves when the stream ends. Throws HttpError on non-2xx.
 */
export async function streamSSE(url, { method = 'GET', body, headers, signal, onEvent }) {
  const res = await fetch(url, {
    method,
    body,
    signal,
    headers: { Accept: 'text/event-stream', ...(body && typeof body === 'string' ? { 'Content-Type': 'application/json' } : {}), ...headers },
  })
  if (!res.ok) throw new HttpError(res.status, await errorText(res))
  if (!res.body) throw new Error('This browser cannot read streamed responses.')
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    let cut
    while ((cut = buf.indexOf('\n\n')) !== -1) {
      const block = buf.slice(0, cut)
      buf = buf.slice(cut + 2)
      const ev = parseBlock(block)
      if (ev) onEvent(ev)
    }
  }
  buf += decoder.decode()
  if (buf.trim()) {
    const ev = parseBlock(buf)
    if (ev) onEvent(ev)
  }
}

export async function errorText(res) {
  try {
    const t = await res.text()
    try {
      const j = JSON.parse(t)
      const d = j.detail ?? j.error ?? j.message
      if (typeof d === 'string') return d
      if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join('; ')
      return t
    } catch {
      return t || res.statusText
    }
  } catch {
    return res.statusText
  }
}
