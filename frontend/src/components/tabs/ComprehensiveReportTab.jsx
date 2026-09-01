import React, { useState } from 'react';
import { FileCheck, Download, Copy, Check, ExternalLink, ShieldCheck, Sparkles } from 'lucide-react';

export default function ComprehensiveReportTab({ data, onExport }) {
  const [copied, setCopied] = useState(false);

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
        <p>No executive report synthesized yet. Run the full pipeline to compile the report.</p>
      </div>
    );
  }

  const {
    title,
    executive_summary,
    domain_assessment,
    key_insights_summary = [],
    strategic_recommendations = [],
    full_markdown_report,
    generated_at
  } = data;

  const handleCopyMarkdown = () => {
    if (full_markdown_report) {
      navigator.clipboard.writeText(full_markdown_report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner: Actions & Report Header */}
      <div className="glass-card" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.08) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="badge badge-emerald" style={{ fontSize: '10px' }}>
                SYNTHESIZED EXECUTIVE BRIEFING
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Generated {new Date(generated_at).toLocaleString()}
              </span>
            </div>
            <h2 style={{ fontSize: '24px', fontWeight: 800, margin: 0 }} className="gradient-text">
              {title}
            </h2>
          </div>

          {/* Export Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button onClick={() => onExport('html')} className="btn btn-cyan" style={{ fontSize: '13px' }}>
              <Download size={15} />
              <span>Styled HTML</span>
            </button>
            <button onClick={() => onExport('markdown')} className="btn btn-secondary" style={{ fontSize: '13px' }}>
              <Download size={15} />
              <span>Markdown</span>
            </button>
            <button onClick={() => onExport('json')} className="btn btn-secondary" style={{ fontSize: '13px' }}>
              <Download size={15} />
              <span>JSON Data</span>
            </button>
            <button onClick={handleCopyMarkdown} className="btn btn-ghost" style={{ padding: '8px 12px' }} title="Copy Raw Markdown">
              {copied ? <Check size={16} style={{ color: 'var(--accent-emerald)' }} /> : <Copy size={16} />}
            </button>
          </div>
        </div>

        {/* Executive Summary Paragraphs */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          marginTop: '12px'
        }}>
          <h4 style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan-light)', marginBottom: '8px' }}>
            1. Executive Summary
          </h4>
          <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.7, margin: 0, whiteSpace: 'pre-line' }}>
            {executive_summary}
          </p>
        </div>
      </div>

      {/* Strategic Recommendations Grid / Table */}
      {strategic_recommendations.length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles size={18} style={{ color: 'var(--accent-emerald)' }} />
            <h3 style={{ fontSize: '17px', fontWeight: 700, margin: 0 }}>
              Board & Executive Recommendations Matrix
            </h3>
          </div>

          <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Strategic Pillar</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-secondary)' }}>Priority Horizon</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Initiative Action</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)' }}>Projected ROI / Impact</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-secondary)' }}>Accountable Owner</th>
                </tr>
              </thead>
              <tbody>
                {strategic_recommendations.map((rec, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {rec.pillar}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <span className={`badge ${rec.priority.includes('30') ? 'badge-rose' : rec.priority.includes('90') ? 'badge-cyan' : 'badge-indigo'}`}>
                        {rec.priority}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-primary)' }}>
                      {rec.initiative}
                    </td>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--accent-emerald-light)' }}>
                      {rec.expected_roi}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      {rec.owner}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Raw Markdown Report Reader View */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px' }}>
          Complete Synthesized Report View
        </h3>
        <div style={{
          background: 'var(--bg-canvas)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '24px',
          maxHeight: '520px',
          overflowY: 'auto',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          lineHeight: 1.7,
          whiteSpace: 'pre-wrap',
          fontFamily: 'var(--font-mono)'
        }}>
          {full_markdown_report}
        </div>
      </div>
    </div>
  );
}
