import React, { useState } from 'react';
import { X, Key, Shield, Check, Cpu } from 'lucide-react';

const PROVIDER_OPTIONS = [
  { id: 'groq', name: 'Groq Cloud (Ultra Fast)', defaultModel: 'llama-3.3-70b-versatile', keyPlaceholder: 'gsk_...' },
  { id: 'openai', name: 'OpenAI', defaultModel: 'gpt-4o-mini', keyPlaceholder: 'sk-...' },
  { id: 'gemini', name: 'Google Gemini', defaultModel: 'gemini-2.0-flash', keyPlaceholder: 'AIzaSy...' },
  { id: 'ollama', name: 'Ollama (Local)', defaultModel: 'llama3.2', keyPlaceholder: 'Not needed (localhost:11434)' },
  { id: 'mock', name: 'Intelligent Demo Mode', defaultModel: 'mock-analyst', keyPlaceholder: 'No API Key required' }
];

export default function SettingsModal({ isOpen, onClose, activeProvider, onSaveConfig }) {
  const [selectedProvider, setSelectedProvider] = useState(activeProvider || 'groq');
  const [modelName, setModelName] = useState(
    PROVIDER_OPTIONS.find((p) => p.id === activeProvider)?.defaultModel || 'llama-3.3-70b-versatile'
  );
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);

  if (!isOpen) return null;

  const handleProviderChange = (provId) => {
    setSelectedProvider(provId);
    const opt = PROVIDER_OPTIONS.find((p) => p.id === provId);
    if (opt) setModelName(opt.defaultModel);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSaveConfig({
        provider: selectedProvider,
        model: modelName,
        api_key: apiKey
      });
      onClose();
    } catch (err) {
      alert(`Failed to update config: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const currentOption = PROVIDER_OPTIONS.find((p) => p.id === selectedProvider) || PROVIDER_OPTIONS[0];

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 200,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="glass-card" style={{
        width: '100%',
        maxWidth: '520px',
        padding: '30px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.9), 0 0 40px rgba(6, 182, 212, 0.2)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(6, 182, 212, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)'
            }}>
              <Cpu size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>AI Provider & Model Settings</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                Configure the LLM engine powering all 6 analytical agents
              </p>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost" style={{ padding: '6px' }}>
            <X size={20} />
          </button>
        </div>

        {/* Provider Radio Grid */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Select LLM Provider
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
            {PROVIDER_OPTIONS.map((prov) => (
              <div
                key={prov.id}
                onClick={() => handleProviderChange(prov.id)}
                style={{
                  background: selectedProvider === prov.id ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-elevated)',
                  border: `1px solid ${selectedProvider === prov.id ? 'var(--accent-emerald)' : 'var(--border-subtle)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all var(--transition-fast)'
                }}
              >
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: selectedProvider === prov.id ? '#fff' : 'var(--text-primary)' }}>
                    {prov.name}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {prov.defaultModel}
                  </div>
                </div>
                {selectedProvider === prov.id && (
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-emerald)', boxShadow: '0 0 10px var(--accent-emerald)' }} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Model Name Input */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
            Model Identifier
          </label>
          <input
            type="text"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--bg-canvas)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-mono)',
              fontSize: '13px',
              outline: 'none'
            }}
          />
        </div>

        {/* API Key Input */}
        {selectedProvider !== 'mock' && selectedProvider !== 'ollama' && (
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <Key size={13} style={{ color: 'var(--accent-cyan)' }} />
              <span>{selectedProvider.toUpperCase()} API Key</span>
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={currentOption.keyPlaceholder}
              style={{
                width: '100%',
                background: 'var(--bg-canvas)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '10px 14px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '13px',
                outline: 'none'
              }}
            />
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Keys are passed in-memory to your local FastAPI backend and never stored remotely.
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving} className="btn btn-primary">
            {saving ? 'Updating...' : 'Save & Activate'}
          </button>
        </div>
      </div>
    </div>
  );
}
