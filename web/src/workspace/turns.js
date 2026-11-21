// Turn state: built from streamed events (live or replayed) or from a stored Turn.

let seq = 0
export const newTurnId = () => `local-${Date.now().toString(36)}-${++seq}`

export function emptyTurn(question, extra = {}) {
  return {
    id: newTurnId(), question, status: 'planning', steps: [], answer_md: '', key_numbers: [], follow_ups: [],
    ungrounded: null, grounded_count: null, total_numbers: null, error: null, startedAt: Date.now(), ...extra,
  }
}

function planFrom(data) {
  if (Array.isArray(data)) return data
  return data?.plan || data?.steps || []
}

/** A result list item is either {index, tool, args, ok, result|error, ms} or a bare tool result. */
function stepFromResult(r, planStep = {}, i) {
  if (!r) return { index: i, tool: planStep.tool, args: planStep.args || {}, why: planStep.why, status: 'pending' }
  const bare = !('result' in r) && !('ok' in r) && ('data' in r || 'chart' in r)
  const result = bare ? r : r.result
  const ok = bare ? true : r.ok !== false && !r.error
  return {
    index: i,
    tool: r.tool || result?.tool || planStep.tool,
    args: r.args || result?.args || planStep.args || {},
    why: r.why || planStep.why,
    status: ok ? 'done' : 'error',
    ms: r.ms,
    result: ok ? result : null,
    error: ok ? null : r.error || 'Step failed',
  }
}

export function turnFromStored(t, extra = {}) {
  const plan = t.plan || []
  const results = t.results || []
  const n = Math.max(plan.length, results.length)
  const steps = Array.from({ length: n }, (_, i) => {
    const r = results.find((x) => x && x.index === i) || results[i]
    return stepFromResult(r, plan[i] || {}, i)
  })
  return {
    id: t.id || newTurnId(), question: t.question, status: 'done', steps,
    answer_md: t.answer_md || '', key_numbers: t.key_numbers || [], follow_ups: t.follow_ups || [],
    ungrounded: Array.isArray(t.ungrounded) ? t.ungrounded : [],
    grounded_count: t.grounded_count ?? null, total_numbers: t.total_numbers ?? null,
    created_at: t.created_at, error: null, ...extra,
  }
}

function stepIndex(steps, idx) {
  if (typeof idx !== 'number') return steps.findIndex((s) => s.status === 'pending' || s.status === 'running')
  return idx
}

export function applyEvent(turn, { event, data }) {
  switch (event) {
    case 'plan': {
      const plan = planFrom(data)
      const dropped = Array.isArray(data?.dropped) ? data.dropped : []
      return { ...turn, planMode: data?.mode, planNote: data?.note || null, dropped, status: plan.length ? 'running' : 'answering', steps: plan.map((p, i) => ({ index: i, tool: p.tool, args: p.args || {}, why: p.why, status: 'pending' })) }
    }
    case 'tool_start': {
      const steps = [...turn.steps]
      const i = stepIndex(steps, data?.index)
      steps[i] = { ...(steps[i] || { index: i, args: {} }), tool: data?.tool ?? steps[i]?.tool, args: data?.args ?? steps[i]?.args ?? {}, status: 'running', t0: Date.now() }
      return { ...turn, status: 'running', steps }
    }
    case 'tool_result': {
      const steps = [...turn.steps]
      const i = stepIndex(steps, data?.index)
      const prev = steps[i] || {}
      const s = stepFromResult(data, prev, i)
      steps[i] = { ...prev, ...s, why: prev.why || s.why, ms: data?.ms ?? (prev.t0 ? Date.now() - prev.t0 : undefined) }
      const allDone = steps.every((x) => x.status === 'done' || x.status === 'error')
      return { ...turn, steps, status: allDone ? 'answering' : 'running' }
    }
    case 'answer':
      return { ...turn, status: 'checking', answer_md: data?.answer_md ?? (typeof data === 'string' ? data : ''), key_numbers: data?.key_numbers || [], follow_ups: data?.follow_ups || [] }
    case 'grounding':
      return {
        ...turn,
        ungrounded: data?.ungrounded || [],
        grounded_count: data?.grounded_count ?? null,
        total_numbers: data?.total_numbers ?? null,
      }
    case 'done': {
      if (data && typeof data === 'object' && (data.answer_md !== undefined || data.plan)) {
        const stored = turnFromStored(data.turn || data)
        return { ...stored, id: turn.id, serverId: stored.id, planMode: turn.planMode, planNote: turn.planNote, dropped: turn.dropped, recorded: turn.recorded, startedAt: turn.startedAt, finishedAt: Date.now() }
      }
      if (data?.turn) return { ...turnFromStored(data.turn), id: turn.id, recorded: turn.recorded, startedAt: turn.startedAt, finishedAt: Date.now() }
      return { ...turn, status: 'done', ungrounded: turn.ungrounded ?? [], finishedAt: Date.now() }
    }
    case 'error':
      return { ...turn, status: 'error', error: data?.message || data?.error || data?.detail || (typeof data === 'string' ? data : 'Something went wrong') }
    default:
      return turn
  }
}

/** Recreate the event sequence of a stored turn so a recording plays through the same code path. */
export function replayEvents(t) {
  const plan = t.plan || []
  const evs = [{ event: 'plan', data: { plan }, wait: 500 }]
  ;(t.results || []).forEach((r, i) => {
    evs.push({ event: 'tool_start', data: { index: i, tool: r.tool, args: r.args }, wait: 260 })
    evs.push({ event: 'tool_result', data: { ...r, index: i }, wait: 380 + (r.ms || 40) * 6 })
  })
  evs.push({ event: 'answer', data: { answer_md: t.answer_md, key_numbers: t.key_numbers, follow_ups: t.follow_ups }, wait: 900 })
  evs.push({ event: 'grounding', data: { ungrounded: t.ungrounded, grounded_count: t.grounded_count, total_numbers: t.total_numbers }, wait: 600 })
  evs.push({ event: 'done', data: t, wait: 150 })
  return evs
}

export const norm = (s) => String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()

export function phaseText(turn) {
  const n = turn.steps.length
  const done = turn.steps.filter((s) => s.status === 'done' || s.status === 'error').length
  switch (turn.status) {
    case 'planning': return 'Choosing which tools to run'
    case 'running': return `Running step ${Math.min(n, done + 1)} of ${n}`
    case 'answering': return 'Writing the answer from the results'
    case 'checking': return 'Checking every number against the results'
    case 'done': return 'Done'
    case 'error': return 'Stopped with an error'
    default: return ''
  }
}

export function argSummary(tool, args = {}) {
  const parts = []
  const a = { ...args }
  const filters = a.filters
  delete a.filters
  if (a.agg && a.metric) { parts.push(`${a.agg}(${a.metric})`); delete a.agg; delete a.metric }
  for (const [k, v] of Object.entries(a)) {
    if (v === undefined || v === null || v === '') continue
    parts.push(`${k} ${Array.isArray(v) ? v.join(', ') : typeof v === 'object' ? JSON.stringify(v) : v}`)
  }
  if (Array.isArray(filters) && filters.length) {
    parts.push('where ' + filters.map((f) => `${f.column} ${f.op} ${Array.isArray(f.value) ? f.value.join('–') : JSON.stringify(f.value)}`).join(' and '))
  }
  return parts.join(' · ')
}
