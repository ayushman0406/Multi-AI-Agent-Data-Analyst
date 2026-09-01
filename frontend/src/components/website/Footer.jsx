import React from 'react';
import { Cpu, ArrowUp, Heart } from 'lucide-react';

export default function Footer() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer style={{
      borderTop: '1px solid var(--border-subtle)',
      background: 'rgba(8, 12, 20, 0.95)',
      padding: '60px 28px 40px',
      marginTop: '80px'
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '40px'
      }}>
        {/* Top Row */}
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '30px'
        }}>
          <div style={{ maxWidth: '380px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.3) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-cyan-light)'
              }}>
                <Cpu size={18} />
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: 800, margin: 0 }}>
                MULTI-AGENT <span className="gradient-text">DATA ANALYST</span>
              </h3>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
              An enterprise-grade autonomous intelligence system combining high-speed DuckDB analytics,
              Pydantic structured output, and 6 specialized AI agents.
            </p>
          </div>

          {/* Nav Links */}
          <div style={{ display: 'flex', gap: '48px', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#fff', marginBottom: '14px' }}>
                Navigation
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
                <a href="#studio" className="nav-link">Live Studio</a>
                <a href="#agents" className="nav-link">6-Agent Suite</a>
                <a href="#engine" className="nav-link">DuckDB Engine</a>
                <a href="#faq" className="nav-link">FAQ & Architecture</a>
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#fff', marginBottom: '14px' }}>
                Tech Stack
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px', color: 'var(--text-muted)' }}>
                <span>DuckDB Vectorized C++</span>
                <span>FastAPI Async SSE</span>
                <span>React + Vite Frontend</span>
                <span>Interactive Plotly.js</span>
              </div>
            </div>
          </div>

          {/* Back to top button */}
          <div>
            <button
              onClick={scrollToTop}
              className="btn btn-secondary"
              style={{ padding: '10px 16px', fontSize: '12px' }}
            >
              <ArrowUp size={15} />
              <span>Back to Top</span>
            </button>
          </div>
        </div>

        {/* Bottom Row */}
        <div style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          paddingTop: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
          fontSize: '12px',
          color: 'var(--text-muted)'
        }}>
          <div>
            © {new Date().getFullYear()} Multi-AI-Agent Data Analyst. All rights reserved.
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>Architected with</span>
            <Heart size={12} fill="var(--accent-rose)" style={{ color: 'var(--accent-rose)' }} />
            <span>for Modern Data Teams</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
