import React from 'react';
import { Search, TrendingUp, AlertOctagon, Lightbulb, GitFork } from 'lucide-react';

export default function DomainPatternsTab({ data }) {
  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
        <p>No domain pattern analysis available yet. Run the pipeline to discover patterns.</p>
      </div>
    );
  }

  const {
    key_patterns = [],
    notable_correlations = [],
    anomalies_detected = [],
    executive_takeaways = []
  } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Executive Takeaways */}
      {executive_takeaways.length > 0 && (
        <div className="glass-card" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.08) 0%, rgba(99, 102, 241, 0.05) 100%)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Lightbulb size={18} style={{ color: 'var(--accent-cyan)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Executive Domain Insights & Key Takeaways
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
            {executive_takeaways.map((takeaway, i) => (
              <div
                key={i}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 18px',
                  display: 'flex',
                  gap: '12px'
                }}
              >
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: 'rgba(6, 182, 212, 0.2)',
                  color: 'var(--accent-cyan-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: 700,
                  flexShrink: 0
                }}>
                  {i + 1}
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-primary)', margin: 0, lineHeight: 1.5 }}>
                  {takeaway}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Discovered Patterns Cards */}
      <div>
        <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '16px' }}>
          Discovered Multivariate Domain Patterns
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {key_patterns.map((pattern, idx) => (
            <div key={idx} className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--accent-cyan-light)' }}>
                  {pattern.name}
                </h4>
                <span className={`badge ${pattern.confidence === 'high' ? 'badge-emerald' : 'badge-cyan'}`}>
                  {pattern.confidence} confidence
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: 1.5 }}>
                {pattern.description}
              </p>
              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 14px',
                borderLeft: '3px solid var(--accent-emerald)'
              }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                  Business Implication
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginTop: '2px' }}>
                  {pattern.business_implication}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pairwise Significant Correlations */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <GitFork size={18} style={{ color: 'var(--accent-emerald)' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
            Statistically Significant Pairwise Correlations
          </h3>
        </div>

        {notable_correlations.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px' }}>
            {notable_correlations.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 16px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '13px' }}>
                    <span>{item.col1}</span>
                    <span style={{ color: 'var(--text-muted)' }}>⟷</span>
                    <span>{item.col2}</span>
                  </div>
                  <span className={`badge ${Math.abs(item.correlation) >= 0.6 ? 'badge-emerald' : 'badge-cyan'}`}>
                    r = {item.correlation > 0 ? `+${item.correlation}` : item.correlation}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
                  {item.interpretation}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            No strong linear pairwise correlations (r &gt;= 0.3) detected in this dataset.
          </p>
        )}
      </div>

      {/* Anomalies Detected */}
      {anomalies_detected.length > 0 && (
        <div className="glass-card" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <AlertOctagon size={18} style={{ color: 'var(--accent-amber)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Statistical Anomalies & Distribution Outliers
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {anomalies_detected.map((anomaly, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(245, 158, 11, 0.05)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 14px',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-amber)' }} />
                <span>{anomaly}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
