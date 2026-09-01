import React from 'react';
import { FileText, Search, PieChart, Terminal, Target, FileCheck, CheckCircle2, ArrowRight } from 'lucide-react';

const AGENTS = [
  {
    id: '01',
    title: 'Dataset Description Agent',
    icon: FileText,
    accent: 'var(--accent-emerald)',
    badge: 'Foundation & Lineage',
    summary: 'Vectorized schema profiling, semantic data type classification, missingness auditing, and business process context identification.',
    features: [
      'Semantic role detection (ID, metrics, categories, currencies)',
      'Vectorized statistical profiling (mean, stddev, quantiles)',
      'Automated data quality & anomaly diagnostic alerts'
    ]
  },
  {
    id: '02',
    title: 'Domain Patterns Agent',
    icon: Search,
    accent: 'var(--accent-cyan)',
    badge: 'Pattern Discovery',
    summary: 'Analyzes cross-variable dependencies, pairwise Pearson correlations, and multi-variate clustering unique to the business domain.',
    features: [
      'Pairwise statistical correlation strength assessment',
      'Multivariate domain pattern recognition with confidence scoring',
      'Anomaly flagging for tail-event cluster behaviors'
    ]
  },
  {
    id: '03',
    title: 'Interactive Visualizations Agent',
    icon: PieChart,
    accent: 'var(--accent-indigo)',
    badge: 'Plotly Visualization',
    summary: 'Generates dynamic, fully interactive Plotly chart specifications configured with Midnight Luxe obsidian palettes and hover tooltips.',
    features: [
      'Dynamic correlation heatmaps and distribution histograms',
      'Categorical demographic breakdowns and bivariate scatter plots',
      'Client-side responsive rendering with zoom, pan, and PNG export'
    ]
  },
  {
    id: '04',
    title: 'Custom & Statistical Analysis Agent',
    icon: Terminal,
    accent: 'var(--accent-violet)',
    badge: 'Hypothesis Testing',
    summary: 'Executes formal statistical hypothesis tests, calculates feature influence rankings towards target metrics, and sandboxes analytical code.',
    features: [
      'D\'Agostino-Pearson normality & Welch\'s two-sample t-tests',
      'Mathematical key driver ranking towards outcome metrics',
      'Restricted sandboxed Python execution environment'
    ]
  },
  {
    id: '05',
    title: 'Strategic Business Goals Agent',
    icon: Target,
    accent: 'var(--accent-amber)',
    badge: 'Commercial KPIs',
    summary: 'Translates quantitative empirical observations into commercial strategy, monetization avenues, and prioritized action matrices.',
    features: [
      'Strategic goal categorization (Revenue, Cost, Risk, Retention)',
      'Actionable revenue levers and operational risk identification',
      'Priority implementation matrix (Impact vs Effort vs Horizon)'
    ]
  },
  {
    id: '06',
    title: 'Comprehensive Executive Report Agent',
    icon: FileCheck,
    accent: 'var(--accent-emerald-light)',
    badge: 'Executive Synthesis',
    summary: 'Synthesizes all 5 upstream agent telemetry streams into a unified executive report, available in Markdown and standalone styled HTML.',
    features: [
      'C-suite executive summary & domain context briefing',
      'Structured board recommendation matrix with ROI estimates',
      'Instant 1-click downloads for Markdown, styled HTML, and JSON'
    ]
  }
];

export default function AgentSuiteSection() {
  return (
    <section id="agents" style={{ padding: '80px 0', borderTop: '1px solid var(--border-subtle)' }}>
      <div className="section-header">
        <span className="badge badge-cyan" style={{ marginBottom: '12px' }}>
          Autonomous Multi-Agent Suite
        </span>
        <h2>Six Specialized Intelligence Agents</h2>
        <p>
          Each agent operates with deep domain specialization, communicating through a shared
          type-safe state context to deliver comprehensive, trustworthy analytical deliverables.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: '24px'
      }}>
        {AGENTS.map((agent) => {
          const Icon = agent.icon;
          return (
            <div key={agent.id} className="glass-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid rgba(255, 255, 255, 0.08)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: agent.accent
                }}>
                  <Icon size={22} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-emerald" style={{ fontSize: '10px' }}>{agent.badge}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>{agent.id}</span>
                </div>
              </div>

              <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '10px' }}>
                {agent.title}
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '20px', flex: 1 }}>
                {agent.summary}
              </p>

              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                border: '1px solid rgba(255, 255, 255, 0.04)'
              }}>
                <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  Agent Capabilities:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {agent.features.map((feat, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-primary)' }}>
                      <CheckCircle2 size={13} style={{ color: agent.accent, flexShrink: 0 }} />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
