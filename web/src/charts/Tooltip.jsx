export default function Tooltip({ tip, width }) {
  if (!tip) return null
  const left = Math.min(Math.max(tip.x, 8), width - 8)
  const flip = tip.x > width * 0.62
  return (
    <div
      className="viz-tip"
      role="status"
      style={{ left, top: tip.y, transform: `translate(${flip ? 'calc(-100% - 12px)' : '12px'}, -50%)` }}
    >
      {tip.title && <div className="viz-tip-title">{tip.title}</div>}
      {tip.rows.map((r, i) => (
        <div className="viz-tip-row" key={i}>
          {r.color && <span className="viz-tip-key" style={{ background: r.color }} aria-hidden="true" />}
          <strong className="tnum">{r.value}</strong>
          {r.name && <span>{r.name}</span>}
        </div>
      ))}
    </div>
  )
}
