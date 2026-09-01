import React from 'react';
import { Target, TrendingUp, AlertTriangle, CheckSquare, Zap, Clock } from 'lucide-react';

export default function BusinessGoalsTab({ data }) {
  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
        <p>No business goals defined yet. Run the pipeline to synthesize strategy.</p>
      </div>
    );
  }

  const {
    strategic_goals = [],
    revenue_optimizations = [],
    risk_factors = [],
    priority_action_matrix = []
  } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Strategic Goals Cards */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Target size={18} style={{ color: 'var(--accent-emerald)' }} />
          <h3 style={{ fontSize: '17px', fontWeight: 700, margin: 0 }}>
            Core Strategic Commercial Objectives
          </h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {strategic_goals.map((goal, idx) => (
            <div key={idx} className="glass-card" style={{ padding: '22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className={`badge ${goal.estimated_impact === 'transformative' ? 'badge-rose' : 'badge-emerald'}`}>
                  {goal.estimated_impact} IMPACT
                </span>
                <span className="badge badge-indigo" style={{ fontSize: '9px' }}>
                  {goal.category.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              <h4 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px', color: '#FFFFFF' }}>
                {goal.goal_title}
              </h4>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '14px' }}>
                {goal.description}
              </p>

              {/* Target Metric Callout */}
              <div style={{
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 14px',
                marginBottom: '14px'
              }}>
                <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--accent-emerald-light)', fontWeight: 700 }}>
                  Target Metric
                </div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {goal.target_metric}
                </div>
              </div>

              {/* Initiatives */}
              {goal.recommended_initiatives?.length > 0 && (
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '6px' }}>
                    Key Action Initiatives:
                  </div>
                  <ul style={{ paddingLeft: '18px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {goal.recommended_initiatives.map((init, i) => (
                      <li key={i} style={{ marginBottom: '4px' }}>{init}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Revenue Optimizations & Risks Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Revenue Opportunities */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <TrendingUp size={18} style={{ color: 'var(--accent-cyan)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Revenue & Monetization Levers
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {revenue_optimizations.map((rev, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', background: 'var(--bg-elevated)', padding: '12px 16px', borderRadius: 'var(--radius-md)' }}>
                <Zap size={16} style={{ color: 'var(--accent-cyan)', flexShrink: 0, marginTop: '2px' }} />
                <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{rev}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Factors */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <AlertTriangle size={18} style={{ color: 'var(--accent-amber)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Strategic & Operational Risk Factors
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {risk_factors.map((risk, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', background: 'var(--bg-elevated)', padding: '12px 16px', borderRadius: 'var(--radius-md)' }}>
                <AlertTriangle size={16} style={{ color: 'var(--accent-amber)', flexShrink: 0, marginTop: '2px' }} />
                <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{risk}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Priority Action Matrix Table */}
      {priority_action_matrix.length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Clock size={18} style={{ color: 'var(--accent-emerald)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Priority Action & Implementation Matrix
            </h3>
          </div>
          <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Action Item</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-secondary)' }}>Projected Impact</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-secondary)' }}>Resource Effort</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>Target Horizon</th>
                </tr>
              </thead>
              <tbody>
                {priority_action_matrix.map((action, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {action.action}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <span className={`badge ${action.impact?.toLowerCase() === 'high' ? 'badge-emerald' : 'badge-cyan'}`}>
                        {action.impact}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      {action.effort}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--accent-cyan-light)', fontWeight: 600 }}>
                      {action.timeline}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
