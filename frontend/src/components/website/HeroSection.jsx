import React from 'react';
import { ArrowRight, Sparkles, Database, Zap, Shield, Cpu, Play, BarChart3, Layers } from 'lucide-react';

export default function HeroSection({ onLaunchStudio, onLoadSample }) {
  return (
    <section style={{ padding: '60px 0 80px', position: 'relative' }}>
      <div style={{ maxWidth: '960px', margin: '0 auto', textAlign: 'center' }}>
        {/* Top Tag */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          padding: '6px 16px',
          borderRadius: 'var(--radius-full)',
          marginBottom: '24px',
          boxShadow: '0 0 20px rgba(16, 185, 129, 0.15)'
        }}>
          <span className="pulse-node" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-emerald)' }} />
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-emerald-light)', letterSpacing: '0.05em' }}>
            ENTERPRISE MULTI-AI-AGENT PLATFORM
          </span>
        </div>

        {/* Main Headline */}
        <h1 style={{
          fontSize: 'clamp(36px, 5.5vw, 64px)',
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: '-0.035em',
          marginBottom: '20px'
        }}>
          Autonomous Data Intelligence.{' '}
          <span className="gradient-text">Engineered for Decision Makers.</span>
        </h1>

        {/* Subtitle */}
        <p style={{
          fontSize: 'clamp(16px, 2vw, 19px)',
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
          maxWidth: '740px',
          margin: '0 auto 36px'
        }}>
          Six specialized AI agents orchestrate end-to-end dataset profiling, domain pattern discovery,
          interactive Plotly visualization, statistical hypothesis testing, and boardroom-ready report synthesis.
        </p>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', flexWrap: 'wrap', marginBottom: '60px' }}>
          <a href="#studio" onClick={onLaunchStudio} className="btn btn-primary" style={{ padding: '14px 28px', fontSize: '15px' }}>
            <span>Launch Live Studio</span>
            <ArrowRight size={17} />
          </a>
          <button onClick={onLoadSample} className="btn btn-secondary" style={{ padding: '14px 26px', fontSize: '15px' }}>
            <Database size={17} style={{ color: 'var(--accent-cyan)' }} />
            <span>Load Demo Dataset</span>
          </button>
          <a href="#architecture" className="btn btn-ghost" style={{ padding: '14px 20px', fontSize: '15px' }}>
            <span>View Architecture</span>
          </a>
        </div>

        {/* Key Performance Metric Badges */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          textAlign: 'left'
        }}>
          <div className="glass-card" style={{ padding: '20px 22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', marginBottom: '6px' }}>
              <Zap size={18} />
              <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' }}>Zero-JVM Engine</span>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#fff' }}>50x Faster</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Vectorized DuckDB vs PySpark</div>
          </div>

          <div className="glass-card" style={{ padding: '20px 22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', marginBottom: '6px' }}>
              <Cpu size={18} />
              <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' }}>Multi-Agent DAG</span>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#fff' }}>6 Agents</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Coordinated sequential handoffs</div>
          </div>

          <div className="glass-card" style={{ padding: '20px 22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-indigo)', marginBottom: '6px' }}>
              <Shield size={18} />
              <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' }}>Type Safety</span>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#fff' }}>100% Pydantic</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Zero dummy strings or regex hacks</div>
          </div>

          <div className="glass-card" style={{ padding: '20px 22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-amber)', marginBottom: '6px' }}>
              <BarChart3 size={18} />
              <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' }}>Visual Analytics</span>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#fff' }}>Interactive</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Plotly zoom, hover, & filter charts</div>
          </div>
        </div>
      </div>
    </section>
  );
}
