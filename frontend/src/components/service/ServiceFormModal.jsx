import React, { useState, useEffect } from 'react';
import {
  Wrench,
  X,
  Calendar,
  Building,
  DollarSign,
  ShieldCheck,
  FileText,
  AlertCircle,
  Hash
} from 'lucide-react';
import Button from '../common/Button';
import { servicesApi } from '../../services/api';
import './ServiceFormModal.css';

export default function ServiceFormModal({
  isOpen,
  onClose,
  productId,
  productName,
  initialRecord = null,
  availableDocuments = [],
  onSuccess
}) {
  const [formData, setFormData] = useState({
    serviceDate: new Date().toISOString().split('T')[0],
    problem: '',
    serviceCenter: '',
    workPerformed: '',
    cost: '',
    warrantyCovered: false,
    notes: '',
    documentId: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialRecord) {
      setFormData({
        serviceDate: initialRecord.serviceDate || new Date().toISOString().split('T')[0],
        problem: initialRecord.problem || '',
        serviceCenter: initialRecord.serviceCenter || '',
        workPerformed: initialRecord.workPerformed || '',
        cost: initialRecord.cost !== null && initialRecord.cost !== undefined ? String(initialRecord.cost) : '',
        warrantyCovered: Boolean(initialRecord.warrantyCovered),
        notes: initialRecord.notes || '',
        documentId: initialRecord.documentId || ''
      });
    } else {
      setFormData({
        serviceDate: new Date().toISOString().split('T')[0],
        problem: '',
        serviceCenter: '',
        workPerformed: '',
        cost: '',
        warrantyCovered: false,
        notes: '',
        documentId: ''
      });
    }
    setError(null);
  }, [initialRecord, isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.problem.trim()) {
      setError('Please describe the problem or reason for service.');
      return;
    }
    if (!formData.serviceCenter.trim()) {
      setError('Please provide the service center or technician name.');
      return;
    }
    if (!formData.workPerformed.trim()) {
      setError('Please describe the work performed or repair actions taken.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload = {
      productId,
      serviceDate: formData.serviceDate,
      problem: formData.problem.trim(),
      serviceCenter: formData.serviceCenter.trim(),
      workPerformed: formData.workPerformed.trim(),
      cost: formData.cost !== '' ? parseFloat(formData.cost) : 0.0,
      warrantyCovered: formData.warrantyCovered,
      notes: formData.notes.trim() || undefined,
      documentId: formData.documentId || undefined
    };

    try {
      if (initialRecord) {
        await servicesApi.update(initialRecord.id, payload);
      } else {
        await servicesApi.create(payload);
      }
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      console.error('Error saving service record:', err);
      setError(err.message || 'Failed to save service history log.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="service-modal-overlay">
      <div className="service-modal-container">
        {/* Header */}
        <div className="service-modal-header">
          <div className="service-modal-title-row">
            <div className="service-header-icon">
              <Wrench size={20} />
            </div>
            <div>
              <h3 className="service-modal-title">
                {initialRecord ? 'Edit Service Record' : 'Log Service / Repair Record'}
              </h3>
              <p className="service-modal-subtitle">
                Asset: <strong>{productName}</strong>
              </p>
            </div>
          </div>
          <button className="service-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="service-modal-form">
          {error && (
            <div className="service-error-alert">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="service-grid-2">
            {/* Service Date */}
            <div className="service-form-group">
              <label className="service-label">
                <Calendar size={13} /> Service Date <span className="req">*</span>
              </label>
              <input
                type="date"
                name="serviceDate"
                className="service-input"
                value={formData.serviceDate}
                onChange={handleChange}
                required
              />
            </div>

            {/* Service Center */}
            <div className="service-form-group">
              <label className="service-label">
                <Building size={13} /> Service Center / Provider <span className="req">*</span>
              </label>
              <input
                type="text"
                name="serviceCenter"
                className="service-input"
                placeholder="e.g. Samsung Authorized Service Center, Apple Genius Bar"
                value={formData.serviceCenter}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          {/* Problem / Defect */}
          <div className="service-form-group">
            <label className="service-label">
              Problem / Symptom Reported <span className="req">*</span>
            </label>
            <input
              type="text"
              name="problem"
              className="service-input"
              placeholder="e.g. Screen flickering with vertical line defect, Battery not charging"
              value={formData.problem}
              onChange={handleChange}
              required
            />
          </div>

          {/* Work Performed */}
          <div className="service-form-group">
            <label className="service-label">
              Work Performed / Repairs <span className="req">*</span>
            </label>
            <textarea
              name="workPerformed"
              className="service-textarea"
              rows={3}
              placeholder="e.g. Replaced display panel module and calibrated touchscreen, updated firmware"
              value={formData.workPerformed}
              onChange={handleChange}
              required
            />
          </div>

          <div className="service-grid-2">
            {/* Cost */}
            <div className="service-form-group">
              <label className="service-label">
                <DollarSign size={13} /> Total Service Cost (₹)
              </label>
              <input
                type="number"
                name="cost"
                min="0"
                step="0.01"
                className="service-input"
                placeholder="0.00"
                value={formData.cost}
                onChange={handleChange}
              />
            </div>

            {/* Warranty Covered Checkbox */}
            <div className="service-form-group checkbox-group">
              <label className="service-checkbox-label">
                <input
                  type="checkbox"
                  name="warrantyCovered"
                  checked={formData.warrantyCovered}
                  onChange={handleChange}
                  className="service-checkbox"
                />
                <div className="checkbox-text">
                  <span className="checkbox-title">
                    <ShieldCheck size={14} className="green" /> Covered by Warranty
                  </span>
                  <span className="checkbox-desc">Check if repaired free under active warranty</span>
                </div>
              </label>
            </div>
          </div>

          {/* Attached Document */}
          <div className="service-form-group">
            <label className="service-label">
              <FileText size={13} /> Attach Service Invoice / Job Sheet Document:
            </label>
            <select
              name="documentId"
              className="service-select"
              value={formData.documentId}
              onChange={handleChange}
            >
              <option value="">-- None (No document attached) --</option>
              {availableDocuments.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.documentType}: {doc.originalFilename}
                </option>
              ))}
            </select>
          </div>

          {/* Notes / RMA / Job Sheet ID */}
          <div className="service-form-group">
            <label className="service-label">
              <Hash size={13} /> Notes, Job Sheet #, or RMA ID:
            </label>
            <input
              type="text"
              name="notes"
              className="service-input"
              placeholder="e.g. Job Sheet #JS-984210, Technician: Ramesh"
              value={formData.notes}
              onChange={handleChange}
            />
          </div>

          {/* Footer */}
          <div className="service-modal-footer">
            <Button variant="secondary" type="button" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? 'Saving...' : initialRecord ? 'Update Record' : 'Save Service Record'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
