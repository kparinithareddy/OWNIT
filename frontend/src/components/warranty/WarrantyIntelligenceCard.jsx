import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
  Building,
  Globe,
  ExternalLink,
  ChevronRight,
  Sparkles,
  PhoneCall,
  Layers,
  ArrowRight,
  RotateCcw,
  Check,
  UploadCloud,
  FileQuestion,
  FileSignature
} from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import Badge from '../common/Badge';
import WarrantyClaimAssistantModal from '../claim/WarrantyClaimAssistantModal';
import { warrantyIntelligenceApi } from '../../services/api';
import './WarrantyIntelligenceCard.css';

const QUICK_QUESTIONS = [
  { id: 'is_active', label: 'Is my warranty active?', icon: ShieldCheck },
  { id: 'what_covered', label: 'What is covered?', icon: Layers },
  { id: 'what_excluded', label: 'What is excluded?', icon: ShieldX },
  { id: 'how_to_claim', label: 'How do I claim?', icon: PhoneCall },
  { id: 'required_documents', label: 'Which documents do I need?', icon: FileText }
];

const ISSUE_PRESETS = [
  { label: 'Screen flickering / Line defect', query: 'Screen flickering with vertical colored line defect' },
  { label: 'Won\'t turn on / Motherboard', query: 'Device not turning on, sudden power failure during normal use' },
  { label: 'Accidental drop / Broken glass', query: 'Device dropped on floor and screen glass cracked' },
  { label: 'Liquid spill / Water ingress', query: 'Accidental liquid water spill on keyboard and casing' },
  { label: 'Motor / Compressor abnormal noise', query: 'Compressor making loud vibrating noise and not cooling' }
];

export default function WarrantyIntelligenceCard({ product, warranties = [], documents = [] }) {
  const [activeTab, setActiveTab] = useState('issue'); // 'issue' | 'quick'
  const [issueQuery, setIssueQuery] = useState('');
  const [selectedQuestion, setSelectedQuestion] = useState('is_active');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showPipeline, setShowPipeline] = useState(true);
  const [isClaimModalOpen, setIsClaimModalOpen] = useState(false);

  // Run initial active status check on mount
  useEffect(() => {
    if (product?.id) {
      handleQuickQuestion('is_active');
    }
  }, [product?.id]);

  const handleAnalyzeIssue = async (customText) => {
    const textToAnalyze = (customText || issueQuery).trim();
    if (!textToAnalyze) return;

    setLoading(true);
    setError(null);
    try {
      const data = await warrantyIntelligenceApi.analyze({
        productId: product.id,
        questionType: 'issue_coverage',
        issueDescription: textToAnalyze
      });
      setResult(data);
      if (customText) setIssueQuery(customText);
    } catch (err) {
      console.error('Error analyzing warranty intelligence:', err);
      setError(err.message || 'Could not analyze warranty intelligence.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuestion = async (qType) => {
    setSelectedQuestion(qType);
    setLoading(true);
    setError(null);
    try {
      const data = await warrantyIntelligenceApi.quickCheck(product.id, qType);
      setResult(data);
    } catch (err) {
      console.error('Error running quick warranty query:', err);
      setError(err.message || 'Could not evaluate warranty query.');
    } finally {
      setLoading(false);
    }
  };

  const getVerdictVisuals = (likelihood) => {
    switch (likelihood) {
      case 'confirmed_coverage':
        return {
          icon: CheckCircle2,
          badgeClass: 'verdict-badge-confirmed',
          cardClass: 'verdict-card-confirmed',
          text: 'Confirmed Coverage'
        };
      case 'likely_coverage':
        return {
          icon: ShieldCheck,
          badgeClass: 'verdict-badge-likely',
          cardClass: 'verdict-card-likely',
          text: 'Likely Coverage'
        };
      case 'excluded_issue':
        return {
          icon: ShieldX,
          badgeClass: 'verdict-badge-excluded',
          cardClass: 'verdict-card-excluded',
          text: 'Excluded Issue / Out of Warranty'
        };
      case 'unclear_coverage':
      default:
        return {
          icon: HelpCircle,
          badgeClass: 'verdict-badge-unclear',
          cardClass: 'verdict-card-unclear',
          text: 'Unclear / Diagnostic Required'
        };
    }
  };

  const verdict = result ? getVerdictVisuals(result.coverageLikelihood) : null;
  const VerdictIcon = verdict?.icon || HelpCircle;

  return (
    <Card className="warranty-intelligence-card" padding="lg">
      {/* Header */}
      <div className="wi-header">
        <div className="wi-header-left">
          <div className="wi-icon-avatar">
            <ShieldAlert size={22} />
          </div>
          <div>
            <h3 className="wi-title">Warranty Intelligence Engine</h3>
            <p className="wi-subtitle">
              Structured 9-step evidence analysis for <strong>{product.brand} {product.name}</strong>
            </p>
          </div>
        </div>
        <div className="wi-header-right">
          <span className="wi-active-pill">
            <span className={`status-dot ${warranties.some(w => w.status === 'Active') ? 'green' : 'red'}`} />
            {warranties.some(w => w.status === 'Active') ? 'Active Coverage Registered' : 'No Active Warranty'}
          </span>
        </div>
      </div>

      {/* Mode Selector Tabs */}
      <div className="wi-nav-tabs">
        <button
          className={`wi-nav-btn ${activeTab === 'issue' ? 'active' : ''}`}
          onClick={() => setActiveTab('issue')}
        >
          <Sparkles size={15} /> Check Specific Issue / Defect
        </button>
        <button
          className={`wi-nav-btn ${activeTab === 'quick' ? 'active' : ''}`}
          onClick={() => setActiveTab('quick')}
        >
          <FileQuestion size={15} /> Quick Policy Inquiries
        </button>
      </div>

      {/* Tab: Specific Issue Analyzer */}
      {activeTab === 'issue' && (
        <div className="wi-issue-section">
          <div className="wi-input-box">
            <label className="wi-input-label">Describe Symptom, Damage, or Malfunction:</label>
            <div className="wi-input-row">
              <input
                type="text"
                className="wi-search-input"
                placeholder="e.g. Screen flickering with vertical green line, dropped phone, water damage..."
                value={issueQuery}
                onChange={(e) => setIssueQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAnalyzeIssue();
                }}
              />
              <Button
                variant="primary"
                onClick={() => handleAnalyzeIssue()}
                disabled={!issueQuery.trim() || loading}
              >
                {loading ? 'Analyzing...' : 'Analyze Coverage'}
              </Button>
            </div>
          </div>

          {/* Issue Presets */}
          <div className="wi-presets-row">
            <span className="wi-presets-label">Common Scenarios:</span>
            {ISSUE_PRESETS.map((preset, idx) => (
              <button
                key={idx}
                className="wi-preset-chip"
                onClick={() => handleAnalyzeIssue(preset.query)}
                disabled={loading}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Quick Questions */}
      {activeTab === 'quick' && (
        <div className="wi-quick-questions-row">
          {QUICK_QUESTIONS.map((q) => {
            const QIcon = q.icon;
            const isSelected = selectedQuestion === q.id;
            return (
              <button
                key={q.id}
                className={`wi-quick-btn ${isSelected ? 'active' : ''}`}
                onClick={() => handleQuickQuestion(q.id)}
                disabled={loading}
              >
                <QIcon size={14} />
                <span>{q.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="wi-error-banner">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Analysis Results Display */}
      {result && (
        <div className="wi-result-wrap">
          {/* Main Verdict Banner */}
          <div className={`wi-verdict-banner ${verdict.cardClass}`}>
            <div className="wi-verdict-header">
              <div className="wi-verdict-title-row">
                <VerdictIcon size={24} className="wi-verdict-icon" />
                <div>
                  <div className="wi-verdict-type-badge">{result.statusLabel || verdict.text}</div>
                  <h4 className="wi-verdict-heading">
                    {result.issueDescription ? `Verdict for: "${result.issueDescription}"` : result.statusLabel}
                  </h4>
                </div>
              </div>
              <div className="wi-confidence-box">
                <span className="confidence-num">{Math.round(result.confidenceScore * 100)}%</span>
                <span className="confidence-txt">Confidence</span>
              </div>
            </div>

            {/* Explanation paragraph */}
            <p className="wi-explanation-text">{result.explanation}</p>

            {/* Mandatory Disclaimer */}
            <div className="wi-disclaimer-box">
              <AlertTriangle size={13} className="disclaimer-icon" />
              <span>{result.disclaimer}</span>
            </div>
          </div>

          {/* Inclusions & Exclusions Breakdown if present */}
          {(result.matchingInclusions?.length > 0 || result.matchingExclusions?.length > 0) && (
            <div className="wi-clauses-grid">
              {result.matchingInclusions?.length > 0 && (
                <div className="wi-clause-col wi-inclusions-box">
                  <h5 className="clause-col-title green">
                    <CheckCircle2 size={14} /> Matched Inclusions & Coverage Rules:
                  </h5>
                  <ul className="clause-list">
                    {result.matchingInclusions.map((inc, i) => (
                      <li key={i}>{inc}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.matchingExclusions?.length > 0 && (
                <div className="wi-clause-col wi-exclusions-box">
                  <h5 className="clause-col-title red">
                    <XCircle size={14} /> Triggered Exclusion Clauses:
                  </h5>
                  <ul className="clause-list">
                    {result.matchingExclusions.map((exc, i) => (
                      <li key={i}>{exc}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Action & Claim Steps */}
          {result.claimSteps && result.claimSteps.length > 0 && (
            <div className="wi-section-card">
              <h5 className="wi-section-title">
                <PhoneCall size={16} /> Recommended Action & Claim Roadmap
              </h5>
              <div className="wi-claim-steps-list">
                {result.claimSteps.map((step, sIdx) => (
                  <div key={sIdx} className="wi-step-item">
                    <div className="wi-step-bullet">{sIdx + 1}</div>
                    <div className="wi-step-text">{step}</div>
                  </div>
                ))}
              </div>

              {result.supportContact && (
                <div className="wi-support-contact-bar">
                  <span className="contact-label">Authorized Support Contact:</span>
                  <span className="contact-val">{result.supportContact}</span>
                </div>
              )}

              <div style={{ marginTop: '8px' }}>
                <Button
                  variant="primary"
                  icon={FileSignature}
                  onClick={() => setIsClaimModalOpen(true)}
                >
                  Prepare Warranty Claim Dossier
                </Button>
              </div>
            </div>
          )}

          {/* Required Documents Checklist */}
          {result.requiredDocuments && result.requiredDocuments.length > 0 && (
            <div className="wi-section-card">
              <h5 className="wi-section-title">
                <FileText size={16} /> Claim Documentation Readiness
              </h5>
              <div className="wi-doc-checklist">
                {result.requiredDocuments.map((docName, dIdx) => {
                  const isAvailable = result.documentsAvailableInVault?.includes(docName);
                  return (
                    <div
                      key={dIdx}
                      className={`wi-doc-check-row ${isAvailable ? 'doc-ready' : 'doc-missing'}`}
                    >
                      {isAvailable ? (
                        <CheckCircle2 size={16} className="doc-icon-ready" />
                      ) : (
                        <AlertTriangle size={16} className="doc-icon-missing" />
                      )}
                      <span className="doc-check-name">{docName}</span>
                      <span className={`doc-status-tag ${isAvailable ? 'tag-ready' : 'tag-missing'}`}>
                        {isAvailable ? 'In Vault' : 'Missing from Vault'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 9-Step Pipeline Visualizer Accordion */}
          {result.pipelineSteps && result.pipelineSteps.length > 0 && (
            <div className="wi-section-card">
              <div
                className="wi-section-title-toggle"
                onClick={() => setShowPipeline(!showPipeline)}
              >
                <div className="toggle-left">
                  <Layers size={16} />
                  <span>9-Step Warranty Analysis Pipeline Breakdown</span>
                </div>
                <span className="toggle-state">{showPipeline ? 'Hide' : 'View Pipeline'}</span>
              </div>

              {showPipeline && (
                <div className="wi-pipeline-flow">
                  {result.pipelineSteps.map((pStep, pIdx) => (
                    <div key={pIdx} className="pipeline-step-node">
                      <div className="step-node-header">
                        <span className="step-node-name">{pStep.stepName}</span>
                        <span className={`step-node-status ${pStep.status.toLowerCase()}`}>
                          {pStep.status}
                        </span>
                      </div>
                      <div className="step-node-details">{pStep.details}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Verified Sourced References */}
          {result.sourceReferences && result.sourceReferences.length > 0 && (
            <div className="wi-sources-card">
              <span className="sources-label-title">
                <ShieldCheck size={14} /> Grounded Sources & Verified Portals:
              </span>
              <div className="wi-sources-list">
                {result.sourceReferences.map((sRef, sIdx) => {
                  const isOEM = sRef.sourceType === 'official_manufacturer';
                  const isDoc = sRef.sourceType === 'user_document';
                  const isExt = sRef.sourceType === 'reliable_external';
                  const Icon = isDoc ? FileText : isOEM ? Building : isExt ? Globe : ShieldCheck;

                  return sRef.url ? (
                    <a
                      key={sIdx}
                      href={sRef.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="wi-source-tag"
                      title={sRef.details || sRef.title}
                    >
                      <Icon size={12} />
                      <span>{sRef.title}</span>
                      {sRef.domain && <span className="source-domain">({sRef.domain})</span>}
                      <ExternalLink size={10} />
                    </a>
                  ) : (
                    <span
                      key={sIdx}
                      className="wi-source-tag"
                      title={sRef.details || sRef.title}
                    >
                      <Icon size={12} />
                      <span>{sRef.title}</span>
                      {sRef.domain && <span className="source-domain">({sRef.domain})</span>}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Warranty Claim Assistant Modal */}
      <WarrantyClaimAssistantModal
        isOpen={isClaimModalOpen}
        onClose={() => setIsClaimModalOpen(false)}
        product={product}
        warranties={warranties}
        initialProblemDescription={result?.issueDescription || issueQuery}
      />
    </Card>
  );
}
