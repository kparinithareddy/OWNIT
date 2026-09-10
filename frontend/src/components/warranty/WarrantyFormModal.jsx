import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Calendar,
  Building,
  Clock,
  Plus,
  Trash2,
  HelpCircle,
  FileCheck,
  AlertCircle,
  PhoneCall,
  Sparkles
} from 'lucide-react';
import Modal from '../common/Modal';
import Input from '../common/Input';
import Button from '../common/Button';
import { WARRANTY_TYPES, DURATION_PRESETS } from '../../data/warrantyTypes';
import { warrantiesApi } from '../../services/api';
import './WarrantyFormModal.css';

function calculateClientExpiry(startDateStr, durationStr) {
  if (!startDateStr || !durationStr) return '';
  const date = new Date(startDateStr);
  if (isNaN(date.getTime())) return '';

  const dur = durationStr.toLowerCase();
  const yearMatch = dur.match(/(\d+)\s*(?:year|yr|y)/);
  const monthMatch = dur.match(/(\d+)\s*(?:month|mo|m)/);
  const dayMatch = dur.match(/(\d+)\s*(?:day|d)/);

  let newDate = new Date(date);
  if (yearMatch) {
    const years = parseInt(yearMatch[1], 10);
    newDate.setFullYear(newDate.getFullYear() + years);
  } else if (monthMatch) {
    const months = parseInt(monthMatch[1], 10);
    newDate.setMonth(newDate.getMonth() + months);
  } else if (dayMatch) {
    const days = parseInt(dayMatch[1], 10);
    newDate.setDate(newDate.getDate() + days);
  } else {
    // Default 1 year
    newDate.setFullYear(newDate.getFullYear() + 1);
  }

  const y = newDate.getFullYear();
  const m = String(newDate.getMonth() + 1).padStart(2, '0');
  const d = String(newDate.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export default function WarrantyFormModal({
  isOpen,
  onClose,
  productId,
  productName = '',
  initialWarranty = null,
  onSuccess
}) {
  const isEditMode = Boolean(initialWarranty && initialWarranty.id);

  const [formData, setFormData] = useState({
    type: 'Comprehensive Warranty',
    customType: '',
    provider: '',
    durationPreset: '1 Year',
    customDuration: '',
    startDate: new Date().toISOString().split('T')[0],
    expiryDate: '',
    conditions: '',
    claimProcedure: '',
    serviceInformation: ''
  });

  const [benefits, setBenefits] = useState([]);
  const [newBenefit, setNewBenefit] = useState('');

  const [exclusions, setExclusions] = useState([]);
  const [newExclusion, setNewExclusion] = useState('');

  const [requiredDocs, setRequiredDocs] = useState(['Purchase Invoice']);
  const [newDoc, setNewDoc] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Initialize or reset form when modal opens
  useEffect(() => {
    if (!isOpen) return;
    setError(null);

    if (initialWarranty) {
      const isPresetType = WARRANTY_TYPES.includes(initialWarranty.type);
      const isPresetDuration = DURATION_PRESETS.some(
        (d) => d.value === initialWarranty.duration
      );

      setFormData({
        type: isPresetType ? initialWarranty.type : 'Other',
        customType: isPresetType ? '' : initialWarranty.type || '',
        provider: initialWarranty.provider || '',
        durationPreset: isPresetDuration ? initialWarranty.duration : 'Custom',
        customDuration: isPresetDuration ? '' : initialWarranty.duration || '',
        startDate: initialWarranty.startDate || new Date().toISOString().split('T')[0],
        expiryDate: initialWarranty.expiryDate || '',
        conditions: initialWarranty.conditions || '',
        claimProcedure: initialWarranty.claimProcedure || '',
        serviceInformation: initialWarranty.serviceInformation || ''
      });
      setBenefits(initialWarranty.benefits || []);
      setExclusions(initialWarranty.exclusions || []);
      setRequiredDocs(initialWarranty.requiredDocuments || ['Purchase Invoice']);
    } else {
      const defaultStart = new Date().toISOString().split('T')[0];
      const defaultExpiry = calculateClientExpiry(defaultStart, '1 Year');
      setFormData({
        type: 'Comprehensive Warranty',
        customType: '',
        provider: '',
        durationPreset: '1 Year',
        customDuration: '',
        startDate: defaultStart,
        expiryDate: defaultExpiry,
        conditions: '',
        claimProcedure: '',
        serviceInformation: ''
      });
      setBenefits(['Free repair / replacement for manufacturing defects', 'Parts & Labor covered']);
      setExclusions(['Physical mishandling or drops', 'Liquid / Water damage']);
      setRequiredDocs(['Purchase Invoice', 'Warranty Card']);
    }
  }, [isOpen, initialWarranty]);

  // Handle duration or start date change to auto-update expiry
  const handleStartDateChange = (val) => {
    setFormData((prev) => {
      const effectiveDur =
        prev.durationPreset === 'Custom' ? prev.customDuration : prev.durationPreset;
      const calculated = calculateClientExpiry(val, effectiveDur);
      return {
        ...prev,
        startDate: val,
        expiryDate: calculated || prev.expiryDate
      };
    });
  };

  const handleDurationPresetChange = (preset) => {
    setFormData((prev) => {
      const effectiveDur = preset === 'Custom' ? prev.customDuration : preset;
      const calculated = calculateClientExpiry(prev.startDate, effectiveDur);
      return {
        ...prev,
        durationPreset: preset,
        expiryDate: calculated || prev.expiryDate
      };
    });
  };

  const handleCustomDurationChange = (val) => {
    setFormData((prev) => {
      const calculated = calculateClientExpiry(prev.startDate, val);
      return {
        ...prev,
        customDuration: val,
        expiryDate: calculated || prev.expiryDate
      };
    });
  };

  // Add / Remove List helpers
  const handleAddBenefit = () => {
    if (newBenefit.trim()) {
      setBenefits((prev) => [...prev, newBenefit.trim()]);
      setNewBenefit('');
    }
  };

  const handleRemoveBenefit = (idx) => {
    setBenefits((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleAddExclusion = () => {
    if (newExclusion.trim()) {
      setExclusions((prev) => [...prev, newExclusion.trim()]);
      setNewExclusion('');
    }
  };

  const handleRemoveExclusion = (idx) => {
    setExclusions((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleAddDoc = () => {
    if (newDoc.trim()) {
      setRequiredDocs((prev) => [...prev, newDoc.trim()]);
      setNewDoc('');
    }
  };

  const handleRemoveDoc = (idx) => {
    setRequiredDocs((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const effectiveType =
      formData.type === 'Other'
        ? formData.customType.trim()
        : formData.type;

    const effectiveDuration =
      formData.durationPreset === 'Custom'
        ? formData.customDuration.trim()
        : formData.durationPreset;

    if (!effectiveType) {
      setError('Warranty type is required.');
      return;
    }
    if (!formData.provider.trim()) {
      setError('Warranty provider / company name is required.');
      return;
    }
    if (!formData.startDate) {
      setError('Start date is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      const payload = {
        productId,
        type: effectiveType,
        provider: formData.provider.trim(),
        duration: effectiveDuration || '1 Year',
        startDate: formData.startDate,
        expiryDate: formData.expiryDate || undefined,
        benefits,
        exclusions,
        conditions: formData.conditions.trim() || undefined,
        claimProcedure: formData.claimProcedure.trim() || undefined,
        requiredDocuments: requiredDocs,
        serviceInformation: formData.serviceInformation.trim() || undefined
      };

      let result;
      if (isEditMode) {
        result = await warrantiesApi.update(initialWarranty.id, payload);
      } else {
        result = await warrantiesApi.create(payload);
      }

      if (onSuccess) onSuccess(result);
      onClose();
    } catch (err) {
      console.error('Error saving warranty:', err);
      setError(err.message || 'Failed to save warranty details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        isEditMode
          ? `Edit Warranty Component`
          : `Add Warranty Component`
      }
      subtitle={productName ? `For ${productName}` : 'Attach coverage terms to this product'}
      size="lg"
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', width: '100%' }}>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            icon={ShieldCheck}
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Saving Coverage...'
              : isEditMode
              ? 'Update Warranty'
              : 'Save Warranty Component'}
          </Button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="warranty-form-container">
        {error && (
          <div className="form-error-banner">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* 1. Type & Provider */}
        <div className="form-section-title">
          <ShieldCheck size={16} /> Component & Provider
        </div>

        <div className="form-grid-2col">
          <div className="input-group">
            <label className="input-label">
              Warranty Type <span className="req">*</span>
            </label>
            <select
              className="form-select"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            >
              {WARRANTY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            {formData.type === 'Other' && (
              <input
                type="text"
                className="form-input"
                style={{ marginTop: '8px' }}
                placeholder="Specify custom warranty type (e.g., Inverter/Motherboard)"
                value={formData.customType}
                onChange={(e) => setFormData({ ...formData, customType: e.target.value })}
                required
              />
            )}
          </div>

          <div className="input-group">
            <label className="input-label">
              Provider / Brand <span className="req">*</span>
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Samsung India, AppleCare+, OneAssist"
              value={formData.provider}
              onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
              required
            />
          </div>
        </div>

        {/* 2. Duration & Timeline */}
        <div className="form-section-title" style={{ marginTop: '16px' }}>
          <Calendar size={16} /> Duration & Coverage Period
        </div>

        <div className="form-grid-3col">
          <div className="input-group">
            <label className="input-label">Duration Preset</label>
            <select
              className="form-select"
              value={formData.durationPreset}
              onChange={(e) => handleDurationPresetChange(e.target.value)}
            >
              {DURATION_PRESETS.map((dp) => (
                <option key={dp.value} value={dp.value}>
                  {dp.label}
                </option>
              ))}
            </select>
            {formData.durationPreset === 'Custom' && (
              <input
                type="text"
                className="form-input"
                style={{ marginTop: '8px' }}
                placeholder="e.g. 18 Months or 4 Years"
                value={formData.customDuration}
                onChange={(e) => handleCustomDurationChange(e.target.value)}
              />
            )}
          </div>

          <div className="input-group">
            <label className="input-label">
              Start Date <span className="req">*</span>
            </label>
            <input
              type="date"
              className="form-input"
              value={formData.startDate}
              onChange={(e) => handleStartDateChange(e.target.value)}
              required
            />
          </div>

          <div className="input-group">
            <label className="input-label">
              Expiry Date
              <span className="helper-pill" title="Auto-calculated from start date & duration. You can manually correct it.">
                Auto / Manual
              </span>
            </label>
            <input
              type="date"
              className="form-input"
              value={formData.expiryDate}
              onChange={(e) => setFormData({ ...formData, expiryDate: e.target.value })}
            />
          </div>
        </div>

        {/* 3. Coverage Benefits & Exclusions */}
        <div className="form-section-title" style={{ marginTop: '16px' }}>
          <Sparkles size={16} /> Covered Benefits & Inclusions
        </div>

        <div className="list-builder-wrap">
          <div className="list-input-row">
            <input
              type="text"
              className="form-input"
              placeholder="Add covered item (e.g., Free screen replacement, Motherboard repair)"
              value={newBenefit}
              onChange={(e) => setNewBenefit(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddBenefit();
                }
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              icon={Plus}
              onClick={handleAddBenefit}
            >
              Add
            </Button>
          </div>
          <div className="tags-cloud">
            {benefits.map((b, i) => (
              <span key={i} className="benefit-tag">
                ✓ {b}
                <button
                  type="button"
                  className="tag-remove-btn"
                  onClick={() => handleRemoveBenefit(i)}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        <div className="form-section-title" style={{ marginTop: '16px' }}>
          <AlertCircle size={16} /> Exclusions & Non-Covered Items
        </div>

        <div className="list-builder-wrap">
          <div className="list-input-row">
            <input
              type="text"
              className="form-input"
              placeholder="Add exclusion (e.g., Liquid spill, Cosmetic scratches)"
              value={newExclusion}
              onChange={(e) => setNewExclusion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddExclusion();
                }
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              icon={Plus}
              onClick={handleAddExclusion}
            >
              Add
            </Button>
          </div>
          <div className="tags-cloud">
            {exclusions.map((ex, i) => (
              <span key={i} className="exclusion-tag">
                ✕ {ex}
                <button
                  type="button"
                  className="tag-remove-btn"
                  onClick={() => handleRemoveExclusion(i)}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* 4. Claim Procedure & Support Info */}
        <div className="form-section-title" style={{ marginTop: '16px' }}>
          <PhoneCall size={16} /> Claim Procedure & Service Contacts
        </div>

        <div className="form-grid-2col">
          <div className="input-group">
            <label className="input-label">Claim Procedure / Instructions</label>
            <textarea
              className="form-textarea"
              rows={3}
              placeholder="Step-by-step claim instructions (e.g., Book home appointment via service app or call toll-free helpline)..."
              value={formData.claimProcedure}
              onChange={(e) => setFormData({ ...formData, claimProcedure: e.target.value })}
            />
          </div>

          <div className="input-group">
            <label className="input-label">Service Contact Information</label>
            <textarea
              className="form-textarea"
              rows={3}
              placeholder="Toll-free number, support email, service website or address..."
              value={formData.serviceInformation}
              onChange={(e) => setFormData({ ...formData, serviceInformation: e.target.value })}
            />
          </div>
        </div>
      </form>
    </Modal>
  );
}
