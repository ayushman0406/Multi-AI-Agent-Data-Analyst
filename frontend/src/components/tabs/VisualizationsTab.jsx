import React, { useEffect, useRef, useState } from 'react';
import { PieChart, Maximize2, Download, Info, Sparkles } from 'lucide-react';

export default function VisualizationsTab({ data }) {
  const [selectedChartIdx, setSelectedChartIdx] = useState(0);
  const chartContainerRef = useRef(null);

  const charts = data?.recommended_charts || [];
  const currentChart = charts[selectedChartIdx];

  useEffect(() => {
    if (!currentChart || !chartContainerRef.current || !window.Plotly) return;

    const { data: plotData = [], layout: plotLayout = {} } = currentChart.figure_json || {};

    const responsiveLayout = {
      ...plotLayout,
      autosize: true,
      paper_bgcolor: '#0B1120',
      plot_bgcolor: '#0F172A',
      font: { color: '#E2E8F0', family: 'Inter, sans-serif' },
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    window.Plotly.newPlot(chartContainerRef.current, plotData, responsiveLayout, config);

    const handleResize = () => {
      if (chartContainerRef.current) {
        window.Plotly.Plots.resize(chartContainerRef.current);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [selectedChartIdx, currentChart]);

  if (!charts.length) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
        <p>No interactive visualizations generated yet. Run the pipeline to render charts.</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Chart Selector Pills */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        overflowX: 'auto',
        paddingBottom: '6px'
      }}>
        {charts.map((chart, idx) => (
          <button
            key={chart.id}
            onClick={() => setSelectedChartIdx(idx)}
            className={`btn ${selectedChartIdx === idx ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '12px', padding: '8px 16px', whiteSpace: 'nowrap' }}
          >
            <PieChart size={14} />
            <span>{chart.title}</span>
          </button>
        ))}
      </div>

      {/* Main Chart Viewer Card */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: 700, margin: 0 }}>
              {currentChart?.title}
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
              {currentChart?.description}
            </p>
          </div>
          <span className="badge badge-cyan">
            {currentChart?.chart_type.toUpperCase()}
          </span>
        </div>

        {/* Plotly Canvas */}
        <div
          ref={chartContainerRef}
          style={{
            width: '100%',
            height: '480px',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            background: '#0B1120'
          }}
        />

        {/* Business Insight Callout */}
        {currentChart?.business_insight && (
          <div style={{
            marginTop: '20px',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(6, 182, 212, 0.05) 100%)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            <Sparkles size={18} style={{ color: 'var(--accent-emerald)', flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--accent-emerald-light)', fontWeight: 700 }}>
                Analytical Takeaway
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-primary)', margin: '4px 0 0' }}>
                {currentChart.business_insight}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Design Rationale Footer */}
      {data?.design_rationale && (
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', margin: 0 }}>
          {data.design_rationale}
        </p>
      )}
    </div>
  );
}
