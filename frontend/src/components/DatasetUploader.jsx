import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, Check, ArrowRight, Table, Sparkles } from 'lucide-react';

export default function DatasetUploader({ onFileUploaded, onLoadSample, currentDataset, previewData }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      onFileUploaded(data);
    } catch (err) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-emerald)' : 'rgba(255, 255, 255, 0.12)'}`,
          background: isDragging
            ? 'rgba(16, 185, 129, 0.06)'
            : 'linear-gradient(180deg, rgba(15, 23, 42, 0.6) 0%, rgba(13, 19, 31, 0.8) 100%)',
          backdropFilter: 'blur(16px)',
          borderRadius: 'var(--radius-xl)',
          padding: '36px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all var(--transition-normal)',
          boxShadow: isDragging ? '0 0 30px rgba(16, 185, 129, 0.2)' : 'var(--shadow-luxe)'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.parquet,.pq,.xlsx,.xls,.json"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files?.[0]) handleUpload(e.target.files[0]);
          }}
        />

        <div style={{
          width: '56px',
          height: '56px',
          margin: '0 auto 16px',
          borderRadius: 'var(--radius-full)',
          background: 'radial-gradient(circle, rgba(6, 182, 212, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--accent-cyan-light)'
        }}>
          <UploadCloud size={28} />
        </div>

        <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>
          {isUploading ? 'Ingesting Dataset & Profiling Schema...' : 'Drop your dataset here, or browse'}
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '440px', margin: '0 auto 14px' }}>
          Supports CSV, Parquet, JSON, and Excel. Loaded directly into our zero-JVM DuckDB vectorized engine.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          <span className="badge badge-cyan" style={{ fontSize: '10px' }}>.CSV</span>
          <span className="badge badge-emerald" style={{ fontSize: '10px' }}>.PARQUET</span>
          <span className="badge badge-indigo" style={{ fontSize: '10px' }}>.XLSX</span>
          <span className="badge badge-amber" style={{ fontSize: '10px' }}>.JSON</span>
        </div>
      </div>

      {/* Dataset Metadata Bar (If loaded) */}
      {currentDataset && (
        <div className="glass-card" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-emerald)'
              }}>
                <FileSpreadsheet size={22} />
              </div>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>
                  {currentDataset.filename}
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                  Ingested & registered as active relational table <code style={{ color: 'var(--accent-cyan)' }}>data</code>
                </p>
              </div>
            </div>

            {/* Metrics pills */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                background: 'var(--bg-elevated)',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Records</div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {currentDataset.total_rows?.toLocaleString()}
                </div>
              </div>

              <div style={{
                background: 'var(--bg-elevated)',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Columns</div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {currentDataset.total_columns}
                </div>
              </div>

              <div style={{
                background: 'var(--bg-elevated)',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Engine</div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                  DuckDB 1.4
                </div>
              </div>
            </div>
          </div>

          {/* Table Preview */}
          {previewData && previewData.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <Table size={15} style={{ color: 'var(--accent-cyan)' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Data Snapshot (First 5 Rows)
                </span>
              </div>
              <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-subtle)' }}>
                      {Object.keys(previewData[0]).map((col) => (
                        <th key={col} style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-secondary)', fontWeight: 600 }}>
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                        {Object.values(row).map((val, cIdx) => (
                          <td key={cIdx} style={{ padding: '8px 14px', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                            {val !== null && val !== undefined ? String(val) : <span style={{ color: 'var(--text-muted)' }}>null</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
