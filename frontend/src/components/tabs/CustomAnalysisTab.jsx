import React from 'react';
import { Terminal, CheckCircle2, XCircle, Award, ListChecks, HelpCircle } from 'lucide-react';

export default function CustomAnalysisTab({ data }) {
  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
        <p>No custom statistical analysis available yet. Run the pipeline to view findings.</p>
      </div>
    );
  }

  const {
    summary,
    statistical_findings = [],
    key_drivers = [],
    actionable_recommendations = []
  } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Executive Summary Card */}
      <div className="glass-card" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.05) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Terminal size={18} style={{ color: 'var(--accent-indigo)' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
            Statistical & Empirical Analysis Briefing
          </h3>
        </div>
        <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.6, margin: 0 }}>
          {summary}
        </p>
      </div>

      {/* Key Drivers Ranking */}
      {key_drivers.length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Award size={18} style={{ color: 'var(--accent-emerald)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Primary Key Driver Impact Ranking
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {key_drivers.map((driver, idx) => (
              <div key={idx} style={{ background: 'var(--bg-elevated)', padding: '12px 18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)' }}>#{idx + 1}</span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>{driver.feature}</span>
                    <span className={`badge ${driver.direction === 'positive' ? 'badge-emerald' : 'badge-rose'}`} style={{ fontSize: '9px' }}>
                      {driver.direction.toUpperCase()} INFLUENCE
                    </span>
                  </div>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-cyan-light)', fontFamily: 'var(--font-mono)' }}>
                    {driver.importance_score}
                  </span>
                </div>

                {/* Progress bar */}
                <div style={{ height: '6px', width: '100%', background: 'rgba(255, 255, 255, 0.08)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min(driver.importance_score * 100, 100)}%`,
                      background: 'linear-gradient(90deg, #06B6D4 0%, #10B981 100%)',
                      borderRadius: 'var(--radius-full)'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hypothesis Testing Table */}
      {statistical_findings.length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>
            Formal Hypothesis Significance Tests
          </h3>
          <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Test Method</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Attributes</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>Test Stat</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>p-Value</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-secondary)' }}>Significance</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {statistical_findings.map((test, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {test.test_name}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {test.columns_tested.join(', ')}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {test.statistic}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', fontFamily: 'var(--font-mono)', color: test.p_value < 0.05 ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                      {test.p_value < 0.0001 ? '< 0.0001' : test.p_value}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <span className={`badge ${test.is_significant ? 'badge-emerald' : 'badge-cyan'}`}>
                        {test.is_significant ? 'p < 0.05' : 'Not Sig'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {test.interpretation}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Actionable Recommendations */}
      {actionable_recommendations.length > 0 && (
        <div className="glass-card" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <ListChecks size={18} style={{ color: 'var(--accent-cyan)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Actionable Modeling & Engineering Recommendations
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {actionable_recommendations.map((rec, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--text-primary)' }}>
                <CheckCircle2 size={16} style={{ color: 'var(--accent-emerald)', flexShrink: 0 }} />
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
