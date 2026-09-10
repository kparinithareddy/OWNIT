import React, { useState, useEffect } from 'react';
import {
  FileSignature,
  X,
  ShieldCheck,
  ShieldAlert,
  FileText,
  Building,
  Globe,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Copy,
  Check,
  Download,
  PhoneCall,
  ExternalLink,
  ChevronRight,
  ArrowLeft,
  Sparkles,
  Layers,
  Info
} from 'lucide-react';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { claimAssistantApi } from '../../services/api';
import './WarrantyClaimAssistantModal.css';

export default function WarrantyClaimAssistantModal({
  isOpen,
  onClose,
  product,
  warranties = [],
  initialWarrantyId = null,
  initialProblemDescription = ''
}) {
  const [step, setStep] = useState(1); // 1: Input, 2: Dossier & Provenance, 3: Review & Draft
  const [selectedWarrantyId, setSelectedWarrantyId] = useState(initialWarrantyId || '');
  const [problemDescription, setProblemDescription] = useState(initialProblemDescription || '');
  const [problemStartDate, setProblemStartDate] = useState('');
  const [incidentDetails, setIncidentDetails] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dossier, setDossier] = useState(null);
  const [editableDraft, setEditableDraft] = useState('');
  const [checklist, setChecklist] = useState([]);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (initialWarrantyId) setSelectedWarrantyId(initialWarrantyId);
    if (initialProblemDescription) setProblemDescription(initialProblemDescription);
    if (warranties.length > 0 && !selectedWarrantyId) {
      const active = warranties.find(w => w.status === 'Active');
      setSelectedWarrantyId(active ? active.id : warranties[0].id);
    }
  }, [initialWarrantyId, initialProblemDescription, warranties, selectedWarrantyId]);

  if (!isOpen || !product) return null;

  const handleGenerateDossier = async () => {
    if (!problemDescription.trim()) {
      setError('Please provide a description of the defect or malfunction.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await claimAssistantApi.prepare({
        productId: product.id,
        warrantyId: selectedWarrantyId || undefined,
        problemDescription: problemDescription.trim(),
        problemStartDate: problemStartDate.trim() || undefined,
        incidentDetails: incidentDetails.trim() || undefined
      });
      setDossier(res);
      setEditableDraft(res.draftSupportMessage);
      setChecklist(res.confirmationChecklist || []);
      setStep(2);
    } catch (err) {
      console.error('Error generating claim dossier:', err);
      setError(err.message || 'Could not prepare warranty claim dossier.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleChecklist = (id) => {
    setChecklist(prev =>
      prev.map(item => (item.id === id ? { ...item, confirmed: !item.confirmed } : item))
    );
  };

  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(editableDraft);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const handleDownloadDossier = () => {
    const textContent = `OWNIT WARRANTY CLAIM PREPARATION DOSSIER
Product: ${dossier.brand} ${dossier.productName} (Model: ${dossier.model})
Generated Date: ${new Date(dossier.createdAt).toLocaleString()}
---------------------------------------------------------

1. PRODUCT & WARRANTY SUMMARY
${dossier.productInfoFields.map(f => `• ${f.label}: ${f.value} [${f.provenance.toUpperCase()}]`).join('\n')}
${dossier.warrantyStatusFields.map(f => `• ${f.label}: ${f.value}`).join('\n')}

2. PROBLEM DESCRIPTION
${dossier.problemSummary.value}

3. CLAIM PROCEDURE
${dossier.claimProcedureSteps.join('\n')}

4. AUTHORIZED SERVICE CONTACT
Brand: ${dossier.serviceContact.brand || ''}
Helpline: ${dossier.serviceContact.helpline || ''}
Support URL: ${dossier.serviceContact.portalUrl || 'N/A'}

---------------------------------------------------------
5. CUSTOMER DRAFT SUPPORT MESSAGE
---------------------------------------------------------
${editableDraft}

---------------------------------------------------------
DISCLAIMER:
${dossier.disclaimer}
`;

    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `warranty_claim_${product.brand.toLowerCase()}_${product.name.toLowerCase().replace(/\s+/g, '_')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderProvenanceBadge = (type) => {
    switch (type) {
      case 'document_verified':
        return (
          <span className="prov-badge prov-doc" title="Directly extracted from uploaded invoice or database record">
            <FileText size={10} /> From Documents
          </span>
        );
      case 'ai_generated':
        return (
          <span className="prov-badge prov-ai" title="Synthesized by AI assistant from your inputs">
            <Sparkles size={10} /> AI-Generated Summary
          </span>
        );
      case 'needs_confirmation':
      default:
        return (
          <span className="prov-badge prov-confirm" title="Requires owner verification before submission">
            <AlertTriangle size={10} /> Needs Confirmation
          </span>
        );
    }
  };

  const allChecklistConfirmed = checklist.length > 0 && checklist.every(c => c.confirmed);

  return (
    <div className="claim-modal-overlay">
      <div className="claim-modal-container">
        {/* Modal Header */}
        <div className="claim-modal-header">
          <div className="claim-header-left">
            <div className="claim-header-icon">
              <FileSignature size={22} />
            </div>
            <div>
              <h3 className="claim-modal-title">Warranty Claim Assistant</h3>
              <p className="claim-modal-subtitle">
                Prepare evidence-grounded claim dossier for <strong>{product.brand} {product.name}</strong>
              </p>
            </div>
          </div>
          <button className="claim-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        {/* Multi-step progress bar */}
        <div className="claim-stepper-bar">
          <div className={`step-node ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            <span className="step-num">{step > 1 ? <Check size={12} /> : '1'}</span>
            <span className="step-label">Problem Details</span>
          </div>
          <div className="step-connector" />
          <div className={`step-node ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
            <span className="step-num">{step > 2 ? <Check size={12} /> : '2'}</span>
            <span className="step-label">Claim Dossier</span>
          </div>
          <div className="step-connector" />
          <div className={`step-node ${step === 3 ? 'active' : ''}`}>
            <span className="step-num">3</span>
            <span className="step-label">Review & Draft</span>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="claim-error-banner">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="claim-modal-body">
          {/* STEP 1: PROBLEM INPUT & WARRANTY SELECTION */}
          {step === 1 && (
            <div className="claim-step-1">
              {/* Warranty Component Selector */}
              <div className="claim-form-group">
                <label className="claim-form-label">
                  Applicable Warranty Component:
                </label>
                {warranties.length > 0 ? (
                  <select
                    className="claim-select"
                    value={selectedWarrantyId}
                    onChange={(e) => setSelectedWarrantyId(e.target.value)}
                  >
                    {warranties.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.type} ({w.provider}) — {w.status} ({w.daysRemaining} days left)
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="claim-no-warranty-box">
                    <AlertTriangle size={15} />
                    <span>No registered warranty components found in vault. Standard manufacturer policy will be used.</span>
                  </div>
                )}
              </div>

              {/* Problem description */}
              <div className="claim-form-group">
                <label className="claim-form-label">
                  Describe Defect / Malfunction <span className="req-star">*</span>
                </label>
                <textarea
                  className="claim-textarea"
                  rows={4}
                  placeholder="Describe the symptoms in detail (e.g. Display screen shows horizontal green lines and flickers periodically, occurred during normal desk use)..."
                  value={problemDescription}
                  onChange={(e) => setProblemDescription(e.target.value)}
                />
              </div>

              {/* Onset date & Troubleshooting */}
              <div className="claim-grid-2">
                <div className="claim-form-group">
                  <label className="claim-form-label">When was it first observed?</label>
                  <input
                    type="date"
                    className="claim-input"
                    value={problemStartDate}
                    onChange={(e) => setProblemStartDate(e.target.value)}
                  />
                </div>
                <div className="claim-form-group">
                  <label className="claim-form-label">Troubleshooting Attempted:</label>
                  <input
                    type="text"
                    className="claim-input"
                    placeholder="e.g. Restarted device, checked cables, ran diagnostics..."
                    value={incidentDetails}
                    onChange={(e) => setIncidentDetails(e.target.value)}
                  />
                </div>
              </div>

              <div className="claim-notice-card">
                <Info size={16} className="notice-icon" />
                <div>
                  <strong>Privacy & Integrity Policy:</strong>
                  <p>
                    OWNIT structures this claim for your direct communication. We will never submit claims or send emails without your review and consent.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: DOSSIER & PROVENANCE REVIEW */}
          {step === 2 && dossier && (
            <div className="claim-step-2">
              {/* Provenance Legend Bar */}
              <div className="provenance-legend-bar">
                <span className="legend-title">Information Sources:</span>
                <span className="prov-badge prov-doc"><FileText size={10} /> Verified Documents</span>
                <span className="prov-badge prov-ai"><Sparkles size={10} /> AI Synthesis</span>
                <span className="prov-badge prov-confirm"><AlertTriangle size={10} /> Needs Confirmation</span>
              </div>

              {/* Product & Warranty Fields */}
              <div className="dossier-section-box">
                <h4 className="dossier-section-title">
                  <Layers size={15} /> 1. Asset & Warranty Status
                </h4>
                <div className="dossier-fields-grid">
                  {dossier.productInfoFields.map((f, idx) => (
                    <div key={idx} className="dossier-field-card">
                      <div className="field-header">
                        <span className="field-label">{f.label}</span>
                        {renderProvenanceBadge(f.provenance)}
                      </div>
                      <div className="field-value">{f.value}</div>
                      {f.notes && <div className="field-notes">{f.notes}</div>}
                    </div>
                  ))}

                  {dossier.warrantyStatusFields.map((f, idx) => (
                    <div key={`w-${idx}`} className="dossier-field-card">
                      <div className="field-header">
                        <span className="field-label">{f.label}</span>
                        {renderProvenanceBadge(f.provenance)}
                      </div>
                      <div className="field-value">{f.value}</div>
                      {f.notes && <div className="field-notes">{f.notes}</div>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Synthesized Problem Summary */}
              <div className="dossier-section-box">
                <div className="field-header">
                  <h4 className="dossier-section-title">
                    <Sparkles size={15} /> 2. Synthesized Defect Narrative
                  </h4>
                  {renderProvenanceBadge(dossier.problemSummary.provenance)}
                </div>
                <div className="problem-summary-callout">
                  {dossier.problemSummary.value}
                </div>
              </div>

              {/* Coverage & Relevant Exclusions */}
              <div className="dossier-grid-2">
                <div className="dossier-section-box">
                  <h4 className="dossier-section-title green">
                    <ShieldCheck size={15} /> 3. Covered Benefits
                  </h4>
                  {dossier.coverageFields.map((cf, idx) => (
                    <div key={idx} className="clause-item">
                      <div className="clause-header">{renderProvenanceBadge(cf.provenance)}</div>
                      <div className="clause-text">{cf.value}</div>
                    </div>
                  ))}
                </div>

                <div className="dossier-section-box">
                  <h4 className="dossier-section-title red">
                    <ShieldAlert size={15} /> 4. Relevant Exclusions
                  </h4>
                  {dossier.relevantExclusions.map((ef, idx) => (
                    <div key={idx} className="clause-item">
                      <div className="clause-header">{renderProvenanceBadge(ef.provenance)}</div>
                      <div className="clause-text">{ef.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Required Documents Checklist */}
              <div className="dossier-section-box">
                <h4 className="dossier-section-title">
                  <FileText size={15} /> 5. Required Claim Documents
                </h4>
                <div className="claim-docs-grid">
                  {dossier.requiredDocuments.map((rd, idx) => (
                    <div key={idx} className={`doc-item-row ${rd.inVault ? 'doc-in-vault' : 'doc-not-in-vault'}`}>
                      {rd.inVault ? <CheckCircle2 size={15} className="green" /> : <AlertTriangle size={15} className="amber" />}
                      <div className="doc-item-text">
                        <span className="doc-name">{rd.name}</span>
                        <span className="doc-notes">{rd.notes}</span>
                      </div>
                      <span className={`doc-tag ${rd.inVault ? 'tag-green' : 'tag-amber'}`}>
                        {rd.inVault ? 'Ready in Vault' : 'Manual Prep Needed'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Official Claim Steps & Contact */}
              <div className="dossier-section-box">
                <h4 className="dossier-section-title">
                  <PhoneCall size={15} /> 6. Claim Procedure & Support Contact
                </h4>
                <div className="claim-steps-column">
                  {dossier.claimProcedureSteps.map((step, sIdx) => (
                    <div key={sIdx} className="procedure-step-row">
                      <span className="procedure-bullet">{sIdx + 1}</span>
                      <span className="procedure-text">{step}</span>
                    </div>
                  ))}
                </div>

                {dossier.serviceContact && (
                  <div className="support-contact-strip">
                    <div className="support-phone">
                      <PhoneCall size={14} /> Helpline: <strong>{dossier.serviceContact.helpline}</strong>
                    </div>
                    {dossier.serviceContact.portalUrl && (
                      <a
                        href={dossier.serviceContact.portalUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="support-portal-link"
                      >
                        <Globe size={14} /> Official Support Portal <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STEP 3: REVIEW & DRAFT SUPPORT MESSAGE */}
          {step === 3 && dossier && (
            <div className="claim-step-3">
              {/* Mandatory Review Checklist */}
              <div className="review-checklist-card">
                <div className="checklist-header">
                  <ShieldCheck size={18} className="green" />
                  <div>
                    <h4 className="checklist-title">Pre-Submission Owner Verification Checklist</h4>
                    <p className="checklist-desc">
                      Please confirm the following declarations before sending your warranty claim:
                    </p>
                  </div>
                </div>

                <div className="checklist-items-wrap">
                  {checklist.map((item) => (
                    <label key={item.id} className={`checklist-item-row ${item.confirmed ? 'confirmed' : ''}`}>
                      <input
                        type="checkbox"
                        checked={item.confirmed}
                        onChange={() => handleToggleChecklist(item.id)}
                        className="checklist-checkbox"
                      />
                      <div className="checklist-item-content">
                        <strong className="checklist-item-label">{item.label}</strong>
                        <span className="checklist-item-desc">{item.description}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Editable Draft Message */}
              <div className="draft-editor-card">
                <div className="draft-editor-header">
                  <div>
                    <h4 className="draft-editor-title">
                      <FileSignature size={16} /> Editable Draft Support Message
                    </h4>
                    <p className="draft-editor-subtitle">
                      You can edit and customize this message before copying or sending.
                    </p>
                  </div>
                  <div className="draft-actions-row">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={Copy}
                      onClick={handleCopyToClipboard}
                    >
                      {copied ? 'Copied!' : 'Copy to Clipboard'}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={Download}
                      onClick={handleDownloadDossier}
                    >
                      Export .TXT
                    </Button>
                  </div>
                </div>

                <textarea
                  className="draft-textarea"
                  rows={14}
                  value={editableDraft}
                  onChange={(e) => setEditableDraft(e.target.value)}
                  placeholder="Your generated warranty claim message..."
                />
              </div>

              {/* Non-submission disclaimer */}
              <div className="claim-disclaimer-card">
                <AlertTriangle size={16} className="disclaimer-icon" />
                <div className="disclaimer-content">
                  <strong>Important Non-Automated Policy:</strong>
                  <p>{dossier.disclaimer}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="claim-modal-footer">
          {step > 1 ? (
            <Button
              variant="secondary"
              icon={ArrowLeft}
              onClick={() => setStep(step - 1)}
            >
              Back
            </Button>
          ) : (
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
          )}

          <div className="footer-right-actions">
            {step === 1 && (
              <Button
                variant="primary"
                onClick={handleGenerateDossier}
                disabled={!problemDescription.trim() || loading}
              >
                {loading ? 'Synthesizing Claim Dossier...' : 'Generate Claim Dossier →'}
              </Button>
            )}

            {step === 2 && (
              <Button
                variant="primary"
                onClick={() => setStep(3)}
              >
                Proceed to Review & Draft Message →
              </Button>
            )}

            {step === 3 && (
              <Button
                variant="primary"
                icon={Copy}
                onClick={handleCopyToClipboard}
                disabled={!editableDraft.trim()}
              >
                {copied ? 'Message Copied!' : 'Copy Finalized Message & Finish'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
