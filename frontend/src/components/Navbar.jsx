import React from 'react';
import { Cpu, Settings, Database, Play, Sparkles, ArrowRight } from 'lucide-react';

export default function Navbar({
  activeProvider,
  onOpenSettings,
  onLoadSample,
  hasDataset,
  isRunning,
  onRunPipeline
}) {
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      background: 'rgba(8, 12, 20, 0.85)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '14px 32px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }}>
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.3) 100%)',
            border: '1px solid rgba(6, 182, 212, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-cyan-light)',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.3)'
          }}>
            <Cpu size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.03em' }}>
                MULTI-AGENT <span className="gradient-text">ANALYST</span>
              </span>
              <span className="badge badge-emerald" style={{ fontSize: '9px', padding: '2px 7px' }}>
                PRO
              </span>
            </div>
          </div>
        </a>
      </div>

      {/* Website Navigation Links */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
        <a href="#" className="nav-link">Overview</a>
        <a href="#agents" className="nav-link">6-Agent Suite</a>
        <a href="#engine" className="nav-link">DuckDB Engine</a>
        <a href="#studio" className="nav-link" style={{ color: 'var(--accent-cyan-light)', fontWeight: 600 }}>
          Live Studio
        </a>
        <a href="#faq" className="nav-link">FAQ</a>
      </nav>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Model Selector Badge */}
        <div
          onClick={onOpenSettings}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--bg-elevated)',
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-subtle)',
            cursor: 'pointer',
            transition: 'border-color var(--transition-fast)'
          }}
          title="Click to configure AI providers and models"
        >
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: activeProvider === 'mock' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
            boxShadow: activeProvider === 'mock' ? '0 0 8px var(--accent-amber)' : '0 0 8px var(--accent-emerald)'
          }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            LLM: <span style={{ color: 'var(--text-primary)' }}>{activeProvider.toUpperCase()}</span>
          </span>
        </div>

        {/* Demo Data shortcut */}
        <button
          onClick={onLoadSample}
          className="btn btn-secondary"
          style={{ fontSize: '12px', padding: '8px 14px' }}
          title="Load pre-packaged sample dataset"
        >
          <Database size={14} style={{ color: 'var(--accent-cyan)' }} />
          <span>Demo Data</span>
        </button>

        {/* Primary CTA */}
        {hasDataset ? (
          <button
            onClick={onRunPipeline}
            disabled={isRunning}
            className="btn btn-primary"
            style={{ fontSize: '13px', padding: '8px 16px' }}
          >
            {isRunning ? (
              <>
                <Sparkles size={14} className="pulse-node" />
                <span>Running Pipeline...</span>
              </>
            ) : (
              <>
                <Play size={14} fill="currentColor" />
                <span>Run Analysis</span>
              </>
            )}
          </button>
        ) : (
          <a href="#studio" className="btn btn-primary" style={{ fontSize: '13px', padding: '8px 16px' }}>
            <span>Open Studio</span>
            <ArrowRight size={14} />
          </a>
        )}

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          className="btn btn-ghost"
          style={{ padding: '8px', borderRadius: 'var(--radius-md)' }}
          title="Settings & API Keys"
        >
          <Settings size={18} />
        </button>
      </div>
    </header>
  );
}
