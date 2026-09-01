import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';
import Navbar from './components/Navbar';
import HeroSection from './components/website/HeroSection';
import AgentSuiteSection from './components/website/AgentSuiteSection';
import BenchmarksSection from './components/website/BenchmarksSection';
import FaqSection from './components/website/FaqSection';
import Footer from './components/website/Footer';
import DatasetUploader from './components/DatasetUploader';
import PipelineStepper from './components/PipelineStepper';
import AgentStudio from './components/AgentStudio';
import DataChatDrawer from './components/DataChatDrawer';
import SettingsModal from './components/SettingsModal';
import { Sparkles, Terminal, Activity, ArrowRight, Play } from 'lucide-react';

export default function App() {
  const [activeProvider, setActiveProvider] = useState('groq');
  const [stages, setStages] = useState([]);
  const [datasetMetadata, setDatasetMetadata] = useState(null);
  const [analysisState, setAnalysisState] = useState(null);
  const [agentProgress, setAgentProgress] = useState({});
  const [activeTab, setActiveTab] = useState('profiler');
  const [isRunning, setIsRunning] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Fetch initial health & configuration
  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        if (data.active_provider) setActiveProvider(data.active_provider);
        if (data.agent_stages) setStages(data.agent_stages);
      })
      .catch((err) => console.error('Failed to fetch health status:', err));
  }, []);

  // Handle Loading Demo Dataset
  const handleLoadSample = async () => {
    try {
      const res = await fetch('/api/sample');
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to load sample');
      setDatasetMetadata(data);
      setAnalysisState(null);
      setAgentProgress({});
      setActiveTab('profiler');

      // Smooth scroll to studio
      const studioEl = document.getElementById('studio');
      if (studioEl) studioEl.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      alert(`Error loading sample: ${err.message}`);
    }
  };

  // Handle User Upload
  const handleFileUploaded = (data) => {
    setDatasetMetadata(data);
    setAnalysisState(null);
    setAgentProgress({});
    setActiveTab('profiler');
  };

  // Run the full 6-agent pipeline with live SSE streaming
  const handleRunPipeline = async () => {
    if (isRunning) return;
    setIsRunning(true);

    try {
      // 1. Open SSE Stream
      const eventSource = new EventSource('/api/pipeline/stream');

      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === 'agent_started') {
            setAgentProgress((prev) => ({
              ...prev,
              [payload.agent_id]: {
                agent_id: payload.agent_id,
                agent_name: payload.agent_name,
                status: 'running',
                progress_pct: payload.overall_pct,
                message: 'Executing agent logic...',
                duration_seconds: 0
              }
            }));
            setActiveTab(payload.agent_id);
          } else if (payload.type === 'agent_completed') {
            setAgentProgress((prev) => ({
              ...prev,
              [payload.agent_id]: {
                agent_id: payload.agent_id,
                agent_name: payload.agent_name,
                status: 'completed',
                progress_pct: payload.overall_pct,
                duration_seconds: payload.duration_seconds,
                message: `Completed in ${payload.duration_seconds}s`
              }
            }));
          } else if (payload.type === 'pipeline_finished') {
            setIsRunning(false);
            eventSource.close();
            if (payload.state) {
              setAnalysisState(payload.state);
              setActiveTab('report');
              confetti({
                particleCount: 90,
                spread: 75,
                origin: { y: 0.6 }
              });
            }
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setIsRunning(false);
        fetchState();
      };

      // 2. Trigger pipeline run
      const runRes = await fetch('/api/pipeline/run', { method: 'POST' });
      if (!runRes.ok) {
        const errData = await runRes.json();
        throw new Error(errData.detail || 'Pipeline run request failed');
      }
    } catch (err) {
      alert(`Pipeline error: ${err.message}`);
      setIsRunning(false);
    }
  };

  const fetchState = async () => {
    try {
      const res = await fetch('/api/state');
      if (res.ok) {
        const stateData = await res.json();
        setAnalysisState(stateData);
      }
    } catch (err) {
      console.warn('Could not fetch state:', err);
    }
  };

  const handleExport = (fmt) => {
    window.open(`/api/export/${fmt}`, '_blank');
  };

  const handleSaveConfig = async (cfg) => {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to update config');
    setActiveProvider(cfg.provider);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <Navbar
        activeProvider={activeProvider}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onLoadSample={handleLoadSample}
        hasDataset={Boolean(datasetMetadata)}
        isRunning={isRunning}
        onRunPipeline={handleRunPipeline}
      />

      {/* Main Website Wrapper */}
      <main style={{ flex: 1, maxWidth: '1280px', width: '100%', margin: '0 auto', padding: '0 28px' }}>
        {/* 1. Hero Section */}
        <HeroSection
          onLaunchStudio={() => {
            const el = document.getElementById('studio');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }}
          onLoadSample={handleLoadSample}
        />

        {/* 2. The 6-Agent Suite Section */}
        <AgentSuiteSection />

        {/* 3. Engine Benchmarks Section */}
        <BenchmarksSection />

        {/* 4. Interactive Live Analyst Studio Section */}
        <section id="studio" style={{ padding: '80px 0', borderTop: '1px solid var(--border-subtle)' }}>
          <div className="section-header">
            <span className="badge badge-emerald" style={{ marginBottom: '12px' }}>
              Interactive Analytics Studio
            </span>
            <h2>Autonomous Workbench</h2>
            <p>
              Upload your dataset below or initialize our pre-configured Heart Disease benchmark dataset
              to trigger the full autonomous analysis pipeline.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            {/* Uploader & Snapshot Zone */}
            <DatasetUploader
              onFileUploaded={handleFileUploaded}
              onLoadSample={handleLoadSample}
              currentDataset={datasetMetadata}
              previewData={datasetMetadata?.preview}
            />

            {/* Stepper & Studio Workspace (Rendered when dataset is loaded) */}
            {datasetMetadata && (
              <>
                <PipelineStepper
                  stages={stages}
                  agentProgress={agentProgress}
                  activeTab={activeTab}
                  onSelectTab={setActiveTab}
                  isRunning={isRunning}
                />

                <AgentStudio
                  activeTab={activeTab}
                  onSelectTab={setActiveTab}
                  state={analysisState}
                  isRunning={isRunning}
                  onExport={handleExport}
                />
              </>
            )}
          </div>
        </section>

        {/* 5. FAQ Section */}
        <FaqSection />
      </main>

      {/* Website Footer */}
      <Footer />

      {/* Floating Chat Drawer */}
      <DataChatDrawer
        isOpen={isChatOpen}
        onToggle={() => setIsChatOpen(!isChatOpen)}
        hasDataset={Boolean(datasetMetadata)}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        activeProvider={activeProvider}
        onSaveConfig={handleSaveConfig}
      />
    </div>
  );
}
