import React from 'react';
import {
  FileText,
  Search,
  PieChart,
  Terminal,
  Target,
  FileCheck,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2
} from 'lucide-react';

const STAGE_ICONS = {
  profiler: FileText,
  patterns: Search,
  visualizations: PieChart,
  custom_analysis: Terminal,
  business_goals: Target,
  report: FileCheck
};

export default function PipelineStepper({
  stages,
  agentProgress,
  activeTab,
  onSelectTab,
  isRunning
}) {
  return (
    <div className="glass-card" style={{ padding: '24px 28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h3 style={{ fontSize: '17px', fontWeight: 700, margin: 0 }}>
            Autonomous Multi-Agent Workflow DAG
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
            Sequential multi-agent handoffs with shared state context
          </p>
        </div>
        {isRunning && (
          <div className="badge badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Loader2 size={12} className="pulse-node" style={{ animation: 'spin 1s linear infinite' }} />
            <span>Orchestrating Live Execution</span>
          </div>
        )}
      </div>

      {/* Stepper Node Graph */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: '14px',
        position: 'relative'
      }}>
        {stages.map((stage, idx) => {
          const progress = agentProgress[stage.id] || { status: 'waiting', message: '', duration_seconds: 0 };
          const Icon = STAGE_ICONS[stage.id] || FileText;
          const isSelected = activeTab === stage.id;
          const isRunningNode = progress.status === 'running';
          const isComplete = progress.status === 'completed';
          const isError = progress.status === 'error';

          return (
            <div
              key={stage.id}
              onClick={() => onSelectTab(stage.id)}
              style={{
                background: isSelected
                  ? 'linear-gradient(180deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.9) 100%)'
                  : 'var(--bg-elevated)',
                border: `1px solid ${
                  isRunningNode
                    ? 'var(--accent-emerald)'
                    : isSelected
                    ? 'var(--accent-cyan)'
                    : isComplete
                    ? 'rgba(16, 185, 129, 0.3)'
                    : 'var(--border-subtle)'
                }`,
                borderRadius: 'var(--radius-lg)',
                padding: '16px 14px',
                cursor: 'pointer',
                transition: 'all var(--transition-normal)',
                position: 'relative',
                boxShadow: isRunningNode
                  ? '0 0 20px rgba(16, 185, 129, 0.3)'
                  : isSelected
                  ? '0 0 15px rgba(6, 182, 212, 0.2)'
                  : 'none'
              }}
            >
              {/* Step indicator pill */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  color: isComplete ? 'var(--accent-emerald)' : 'var(--text-muted)'
                }}>
                  STAGE 0{stage.step}
                </span>

                {/* Status icon badge */}
                <div>
                  {isRunningNode && (
                    <div className="pulse-node" style={{
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      background: 'var(--accent-emerald)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Loader2 size={11} color="#fff" style={{ animation: 'spin 1s linear infinite' }} />
                    </div>
                  )}
                  {isComplete && (
                    <CheckCircle2 size={16} style={{ color: 'var(--accent-emerald)' }} />
                  )}
                  {isError && (
                    <AlertCircle size={16} style={{ color: 'var(--accent-rose)' }} />
                  )}
                  {progress.status === 'waiting' && (
                    <Clock size={14} style={{ color: 'var(--text-muted)' }} />
                  )}
                </div>
              </div>

              {/* Node Icon & Name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  background: isComplete
                    ? 'rgba(16, 185, 129, 0.15)'
                    : isRunningNode
                    ? 'rgba(6, 182, 212, 0.2)'
                    : 'rgba(255, 255, 255, 0.05)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: isComplete ? 'var(--accent-emerald-light)' : isRunningNode ? 'var(--accent-cyan-light)' : 'var(--text-secondary)'
                }}>
                  <Icon size={16} />
                </div>
                <div style={{
                  fontSize: '13px',
                  fontWeight: 700,
                  color: isSelected ? '#FFFFFF' : 'var(--text-primary)',
                  lineHeight: 1.2
                }}>
                  {stage.name.replace(' Agent', '')}
                </div>
              </div>

              {/* Execution Duration / Message */}
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {isComplete && progress.duration_seconds > 0
                  ? `Completed in ${progress.duration_seconds}s`
                  : isRunningNode
                  ? 'Processing telemetry...'
                  : 'Ready'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
