import React from 'react';
import { FileText, Search, PieChart, Terminal, Target, FileCheck } from 'lucide-react';
import DatasetDescriptionTab from './tabs/DatasetDescriptionTab';
import DomainPatternsTab from './tabs/DomainPatternsTab';
import VisualizationsTab from './tabs/VisualizationsTab';
import CustomAnalysisTab from './tabs/CustomAnalysisTab';
import BusinessGoalsTab from './tabs/BusinessGoalsTab';
import ComprehensiveReportTab from './tabs/ComprehensiveReportTab';

const TAB_CONFIG = [
  { id: 'profiler', label: 'Dataset Profiler', icon: FileText, countKey: 'column_statistics' },
  { id: 'patterns', label: 'Domain Patterns', icon: Search, countKey: 'key_patterns' },
  { id: 'visualizations', label: 'Visualizations', icon: PieChart, countKey: 'recommended_charts' },
  { id: 'custom_analysis', label: 'Custom Analysis', icon: Terminal, countKey: 'statistical_findings' },
  { id: 'business_goals', label: 'Business Goals', icon: Target, countKey: 'strategic_goals' },
  { id: 'report', label: 'Executive Report', icon: FileCheck, isPrimary: true },
];

export default function AgentStudio({
  activeTab,
  onSelectTab,
  state,
  isRunning,
  onExport
}) {
  const renderTabContent = () => {
    switch (activeTab) {
      case 'profiler':
        return <DatasetDescriptionTab data={state?.dataset_description} />;
      case 'patterns':
        return <DomainPatternsTab data={state?.domain_patterns} />;
      case 'visualizations':
        return <VisualizationsTab data={state?.visualizations} />;
      case 'custom_analysis':
        return <CustomAnalysisTab data={state?.custom_analysis} />;
      case 'business_goals':
        return <BusinessGoalsTab data={state?.business_goals} />;
      case 'report':
        return <ComprehensiveReportTab data={state?.comprehensive_report} onExport={onExport} />;
      default:
        return <DatasetDescriptionTab data={state?.dataset_description} />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Tab Navigation Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        overflowX: 'auto',
        background: 'var(--bg-card)',
        backdropFilter: 'blur(16px)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '6px'
      }}>
        {TAB_CONFIG.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 18px',
                borderRadius: 'var(--radius-md)',
                background: isActive
                  ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%)'
                  : 'transparent',
                border: `1px solid ${isActive ? 'rgba(16, 185, 129, 0.4)' : 'transparent'}`,
                color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
                fontFamily: 'var(--font-heading)',
                fontSize: '13px',
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                whiteSpace: 'nowrap'
              }}
            >
              <Icon size={16} style={{ color: isActive ? 'var(--accent-emerald)' : 'var(--text-muted)' }} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Active Tab View */}
      <div>{renderTabContent()}</div>
    </div>
  );
}
