import React, { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';

const FAQS = [
  {
    q: 'Which LLM models and providers can I use?',
    a: 'The platform features a multi-provider gateway supporting Groq (Llama 3.3 70B), OpenAI (GPT-4o, GPT-4o-mini), Google Gemini (Gemini 2.0 Flash / Pro), and Ollama for fully offline local models. An intelligent Demo Mode is also included so you can test all features without any API keys.'
  },
  {
    q: 'What file formats and dataset sizes are supported?',
    a: 'The platform ingests CSV, Parquet, JSON, and Excel (.xlsx/.xls) files directly into in-memory DuckDB. It can comfortably process hundreds of thousands of records in sub-second speeds thanks to DuckDB vectorized columnar execution.'
  },
  {
    q: 'How do the 6 agents communicate with each other?',
    a: 'The agents are coordinated via an asynchronous DAG Orchestrator with a unified AnalysisState context. Agent 1 (Profiler) inspects the schema and attaches semantic context, which informs Agent 2 (Domain Patterns) and Agent 3 (Visualizations). Finally, Agent 6 (Report Agent) synthesizes all findings into a unified executive report.'
  },
  {
    q: 'Is my data private and secure?',
    a: 'Yes. All data ingestion, schema parsing, and statistical computations occur entirely on your local machine within in-memory DuckDB and Pandas. When LLM reasoning is requested, only column statistics and anonymized schema samples are passed to the model—never your full raw dataset.'
  },
  {
    q: 'How do I export the analysis and reports?',
    a: 'You can download the generated deliverables in three formats: a GitHub-flavored Markdown report (.md), a standalone styled HTML report (.html) that opens in any browser, or the complete JSON state bundle (.json).'
  }
];

export default function FaqSection() {
  const [openIdx, setOpenIdx] = useState(0);

  return (
    <section id="faq" style={{ padding: '80px 0', borderTop: '1px solid var(--border-subtle)' }}>
      <div className="section-header">
        <span className="badge badge-indigo" style={{ marginBottom: '12px' }}>
          Frequently Asked Questions
        </span>
        <h2>Everything You Need to Know</h2>
        <p>
          Architecture, security, model support, and execution details.
        </p>
      </div>

      <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {FAQS.map((faq, idx) => {
          const isOpen = openIdx === idx;
          return (
            <div
              key={idx}
              className="glass-card"
              style={{
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                borderColor: isOpen ? 'var(--border-active)' : 'var(--border-subtle)'
              }}
            >
              <button
                onClick={() => setOpenIdx(isOpen ? null : idx)}
                style={{
                  width: '100%',
                  padding: '20px 24px',
                  background: 'transparent',
                  border: 'none',
                  color: '#fff',
                  fontSize: '15px',
                  fontWeight: 700,
                  fontFamily: 'var(--font-heading)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  textAlign: 'left'
                }}
              >
                <span>{faq.q}</span>
                <ChevronDown
                  size={18}
                  style={{
                    color: isOpen ? 'var(--accent-emerald)' : 'var(--text-muted)',
                    transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform var(--transition-normal)'
                  }}
                />
              </button>

              {isOpen && (
                <div style={{
                  padding: '0 24px 20px',
                  color: 'var(--text-secondary)',
                  fontSize: '14px',
                  lineHeight: 1.6,
                  borderTop: '1px solid rgba(255, 255, 255, 0.04)'
                }}>
                  <p style={{ margin: 0, paddingTop: '12px' }}>{faq.a}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
