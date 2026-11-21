// Client-side markdown export for the recorded example (live sessions use /report.md).
export function recordedReport(session, turns) {
  const u = session.understanding || {}
  const lines = [`# ${u.title || session.dataset?.name}`, '', '> Example session on synthetic data: tool results are real, answer text was written by hand. Exported from the browser; nothing was computed live.', '', u.summary || '', '']
  if (u.quality_notes?.length) lines.push('## Data quality', '', ...u.quality_notes.map((n) => `- ${n}`), '')
  turns.filter((t) => t.status === 'done').forEach((t, i) => {
    lines.push(`## ${i + 1}. ${t.question}`, '')
    t.steps.forEach((s, j) => lines.push(`${j + 1}. \`${s.tool}\` ${JSON.stringify(s.args)}${s.why ? ` — ${s.why}` : ''}`))
    lines.push('', t.answer_md, '')
    if (t.total_numbers !== null) lines.push(`_Grounding: ${t.grounded_count} of ${t.total_numbers} numbers trace to a computed result._`, '')
  })
  return lines.join('\n')
}
