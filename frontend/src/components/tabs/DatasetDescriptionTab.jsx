import React from 'react';
import { Layers, Users, Activity, AlertTriangle, CheckCircle, ShieldCheck, Sparkles } from 'lucide-react';

export default function DatasetDescriptionTab({ data }) {
  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
        <p>No dataset description generated yet. Run the analysis pipeline to inspect.</p>
      </div>
    );
  }

  const {
    business_domain,
    business_processes = [],
    target_personas = [],
    key_entities = [],
    strategic_value,
    column_statistics = {},
    data_quality_issues = [],
    recommended_transformations = []
  } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner: Domain & Strategic Context */}
      <div className="glass-card" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(6, 182, 212, 0.05) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <span className="badge badge-emerald" style={{ fontSize: '11px', padding: '4px 10px' }}>
            Identified Business Domain
          </span>
          <h2 style={{ fontSize: '22px', fontWeight: 800, margin: 0 }}>
            {business_domain || 'General Business Operations'}
          </h2>
        </div>

        <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.6, marginBottom: '18px' }}>
          {strategic_value}
        </p>

        {/* Tags Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {/* Target Personas */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
              <Users size={14} style={{ color: 'var(--accent-cyan)' }} />
              <span>Target Stakeholders</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {target_personas.map((persona, i) => (
                <span key={i} className="badge badge-cyan" style={{ textTransform: 'none', fontSize: '11px' }}>
                  {persona}
                </span>
              ))}
            </div>
          </div>

          {/* Business Processes */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
              <Activity size={14} style={{ color: 'var(--accent-emerald)' }} />
              <span>Supported Processes</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {business_processes.map((proc, i) => (
                <span key={i} className="badge badge-emerald" style={{ textTransform: 'none', fontSize: '11px' }}>
                  {proc}
                </span>
              ))}
            </div>
          </div>

          {/* Key Entities */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
              <Layers size={14} style={{ color: 'var(--accent-indigo)' }} />
              <span>Core Entities</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {key_entities.map((entity, i) => (
                <span key={i} className="badge badge-indigo" style={{ textTransform: 'none', fontSize: '11px' }}>
                  {entity}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Data Quality Assessment */}
      {data_quality_issues.length > 0 && (
        <div className="glass-card" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <ShieldCheck size={18} style={{ color: 'var(--accent-emerald)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Automated Data Quality & Lineage Diagnostics
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {data_quality_issues.map((issue, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px'
                }}
              >
                <span className={`badge ${issue.severity === 'critical' || issue.severity === 'high' ? 'badge-rose' : 'badge-amber'}`}>
                  {issue.severity}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {issue.description}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    <strong>Remediation:</strong> {issue.recommendation}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Column Data Dictionary & Statistics */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>
          Technical Schema & Column Statistics Dictionary
        </h3>
        <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-subtle)' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Column Name</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Type</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Semantic Role</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>Missing / Null</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>Distinct</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>Min / Max</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>Mean ± Std</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(column_statistics).map(([colName, stat]) => (
                <tr key={colName} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {colName}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {stat.data_type}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span className="badge badge-cyan" style={{ fontSize: '10px' }}>
                      {stat.semantic_type}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    {stat.null_count > 0 ? (
                      <span style={{ color: 'var(--accent-rose)', fontWeight: 600 }}>
                        {stat.null_count} ({stat.null_percentage}%)
                      </span>
                    ) : (
                      <span style={{ color: 'var(--accent-emerald)' }}>0 (0%)</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-primary)' }}>
                    {stat.unique_count.toLocaleString()}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>
                    {stat.min_val !== null && stat.min_val !== undefined
                      ? `${stat.min_val} / ${stat.max_val}`
                      : '—'}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>
                    {stat.mean_val !== null && stat.mean_val !== undefined
                      ? `${stat.mean_val} ± ${stat.stddev_val}`
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
