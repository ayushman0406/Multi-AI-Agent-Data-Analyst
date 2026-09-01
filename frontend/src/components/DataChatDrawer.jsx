import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, User, Sparkles, Loader2 } from 'lucide-react';

const SAMPLE_QUESTIONS = [
  "What is the single most critical driver in this dataset?",
  "Explain the highest correlation and its real-world implication.",
  "What operational risk should leadership address in the first 30 days?"
];

export default function DataChatDrawer({ isOpen, onToggle, hasDataset }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm your Senior AI Data Analyst. Ask me anything about your dataset, statistical correlations, or strategic recommendations."
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to get response');

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply || "No response received." }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Sorry, an error occurred: ${err.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        onClick={onToggle}
        className="btn btn-primary"
        style={{
          position: 'fixed',
          bottom: '28px',
          right: '28px',
          zIndex: 90,
          borderRadius: 'var(--radius-full)',
          padding: '14px 22px',
          boxShadow: '0 8px 30px rgba(16, 185, 129, 0.4)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}
      >
        <MessageSquare size={18} />
        <span style={{ fontSize: '14px', fontWeight: 700 }}>Chat with Analyst</span>
        <span className="badge badge-emerald" style={{ fontSize: '9px', background: 'rgba(255, 255, 255, 0.2)' }}>
          AI
        </span>
      </button>

      {/* Slide-over Drawer */}
      {isOpen && (
        <div style={{
          position: 'fixed',
          bottom: '90px',
          right: '28px',
          width: '420px',
          height: '560px',
          zIndex: 100,
          background: 'rgba(11, 17, 32, 0.95)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 30px rgba(16, 185, 129, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(15, 23, 42, 0.6)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(16, 185, 129, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-emerald)'
              }}>
                <Bot size={18} />
              </div>
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: 700, margin: 0 }}>Analyst Assistant</h4>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: 'var(--accent-emerald-light)' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-emerald)' }} />
                  <span>Grounded in Dataset Telemetry</span>
                </div>
              </div>
            </div>
            <button onClick={onToggle} className="btn btn-ghost" style={{ padding: '6px' }}>
              <X size={18} />
            </button>
          </div>

          {/* Messages Container */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px'
          }}>
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  gap: '10px',
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '88%'
                }}
              >
                {msg.role === 'assistant' && (
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: 'rgba(6, 182, 212, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-cyan-light)',
                    flexShrink: 0
                  }}>
                    <Bot size={13} />
                  </div>
                )}
                <div style={{
                  background: msg.role === 'user' ? 'linear-gradient(135deg, #10B981 0%, #059669 100%)' : 'var(--bg-elevated)',
                  color: msg.role === 'user' ? '#FFFFFF' : 'var(--text-primary)',
                  padding: '10px 14px',
                  borderRadius: msg.role === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                  fontSize: '13px',
                  lineHeight: 1.5,
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
                  whiteSpace: 'pre-wrap'
                }}>
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', gap: '10px', alignSelf: 'flex-start' }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: 'rgba(6, 182, 212, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-cyan-light)'
                }}>
                  <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
                </div>
                <div style={{
                  background: 'var(--bg-elevated)',
                  padding: '10px 14px',
                  borderRadius: '14px 14px 14px 2px',
                  fontSize: '12px',
                  color: 'var(--text-muted)'
                }}>
                  Consulting data models...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Starter Questions */}
          {messages.length <= 2 && hasDataset && (
            <div style={{ padding: '0 16px 10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>Suggested Questions:</span>
              {SAMPLE_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '6px 10px',
                    color: 'var(--text-secondary)',
                    fontSize: '11px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = '#fff')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
                >
                  "{q}"
                </button>
              ))}
            </div>
          )}

          {/* Input Footer */}
          <div style={{
            padding: '12px 16px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={hasDataset ? "Ask a question about your data..." : "Upload a dataset first..."}
              disabled={!hasDataset || loading}
              style={{
                flex: 1,
                background: 'var(--bg-canvas)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '10px 14px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none'
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="btn btn-primary"
              style={{ padding: '10px', borderRadius: 'var(--radius-md)' }}
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
