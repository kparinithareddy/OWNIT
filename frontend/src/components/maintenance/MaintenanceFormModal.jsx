import React, { useState, useEffect } from 'react';
import {
  Wrench,
  Calendar,
  DollarSign,
  Building,
  FileText,
  AlertCircle,
  Save,
  Plus
} from 'lucide-react';
import Modal from '../common/Modal';
import Input, { Select } from '../common/Input';
import Button from '../common/Button';
import { maintenanceApi } from '../../services/api';
import './MaintenanceFormModal.css';

const MAINTENANCE_TYPE_OPTIONS = [
  'Routine Servicing',
  'Cleaning',
  'Filter Replacement',
  'Inspection',
  'Battery Service',
  'Calibration',
  'Lubrication',
  'Software Update',
  'Repair',
  'Other'
];

const MAINTENANCE_STATUS_OPTIONS = [
  'Completed',
  'Scheduled',
  'In Progress',
  'Overdue'
];

export default function MaintenanceFormModal({
  isOpen,
  onClose,
  productId,
  productName = '',
  initialRecord = null,
  availableDocuments = [],
  onSuccess
}) {
  const isEditing = Boolean(initialRecord && initialRecord.id);

  const [formData, setFormData] = useState({
    title: '',
    type: 'Routine Servicing',
    status: 'Completed',
    date: new Date().toISOString().split('T')[0],
    nextDueDate: '',
    cost: '',
    serviceProvider: '',
    documentId: '',
    description: '',
    notes: ''
  });

  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setErrorMessage('');

    if (initialRecord) {
      setFormData({
        title: initialRecord.title || '',
        type: initialRecord.type || 'Routine Servicing',
        status: initialRecord.status || 'Completed',
        date: initialRecord.date || new Date().toISOString().split('T')[0],
        nextDueDate: initialRecord.nextDueDate || '',
        cost: initialRecord.cost !== undefined && initialRecord.cost !== null ? String(initialRecord.cost) : '',
        serviceProvider: initialRecord.serviceProvider || '',
        documentId: initialRecord.documentId || '',
        description: initialRecord.description || '',
        notes: initialRecord.notes || ''
      });
    } else {
      setFormData({
        title: '',
        type: 'Routine Servicing',
        status: 'Completed',
        date: new Date().toISOString().split('T')[0],
        nextDueDate: '',
        cost: '',
        serviceProvider: '',
        documentId: '',
        description: '',
        notes: ''
      });
    }
  }, [isOpen, initialRecord]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!formData.title.trim()) {
      return setErrorMessage('Maintenance title is required.');
    }
    if (!formData.date) {
      return setErrorMessage('Date is required.');
    }

    const payload = {
      productId,
      title: formData.title.trim(),
      type: formData.type,
      status: formData.status,
      date: formData.date,
      nextDueDate: formData.nextDueDate || null,
      cost: formData.cost !== '' && !isNaN(Number(formData.cost)) ? parseFloat(formData.cost) : null,
      serviceProvider: formData.serviceProvider.trim() || null,
      documentId: formData.documentId || null,
      description: formData.description.trim(),
      notes: formData.notes.trim() || null
    };

    try {
      setIsSubmitting(true);
      let result;
      if (isEditing) {
        result = await maintenanceApi.update(initialRecord.id, payload);
      } else {
        result = await maintenanceApi.create(payload);
      }

      if (onSuccess) onSuccess(result);
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Failed to save maintenance record.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Edit Maintenance Record' : 'Log Maintenance Event'}
      subtitle={productName ? `For ${productName}` : 'Track servicing, cleaning, or repair history'}
      maxWidth="620px"
    >
      {errorMessage && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 14px',
          backgroundColor: 'var(--danger-light)',
          color: 'var(--danger)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.8125rem',
          marginBottom: '14px'
        }}>
          <AlertCircle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="maint-form-container">
        <Input
          label="Maintenance / Service Title"
          placeholder="e.g. Annual AC Deep Cleaning & Gas Inspection"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          required
          disabled={isSubmitting}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label className="maint-input-label">Service Type</label>
            <select
              className="maint-form-select"
              value={formData.type}
              onChange={(e) => handleChange('type', e.target.value)}
              disabled={isSubmitting}
            >
              {MAINTENANCE_TYPE_OPTIONS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="maint-input-label">Status</label>
            <select
              className="maint-form-select"
              value={formData.status}
              onChange={(e) => handleChange('status', e.target.value)}
              disabled={isSubmitting}
            >
              {MAINTENANCE_STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <Input
            label="Service Date"
            type="date"
            icon={Calendar}
            value={formData.date}
            onChange={(e) => handleChange('date', e.target.value)}
            required
            disabled={isSubmitting}
          />

          <Input
            label="Next Due Date (Optional)"
            type="date"
            icon={Calendar}
            value={formData.nextDueDate}
            onChange={(e) => handleChange('nextDueDate', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <Input
            label="Service Provider / Technician"
            icon={Building}
            placeholder="e.g. Urban Company, Samsung Service Center"
            value={formData.serviceProvider}
            onChange={(e) => handleChange('serviceProvider', e.target.value)}
            disabled={isSubmitting}
          />

          <Input
            label="Cost / Expense (₹)"
            type="number"
            min="0"
            step="0.01"
            icon={DollarSign}
            placeholder="e.g. 1299"
            value={formData.cost}
            onChange={(e) => handleChange('cost', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        {availableDocuments.length > 0 && (
          <div>
            <label className="maint-input-label">Attach Existing Document / Invoice</label>
            <select
              className="maint-form-select"
              value={formData.documentId}
              onChange={(e) => handleChange('documentId', e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">None / No Document Linked</option>
              {availableDocuments.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.originalFilename} ({doc.documentType})
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="maint-input-label">Service Description / Work Done</label>
          <textarea
            className="maint-form-textarea"
            rows={2}
            placeholder="Describe parts cleaned, components replaced, diagnostic results..."
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label className="maint-input-label">Technician Remarks & Notes</label>
          <textarea
            className="maint-form-textarea"
            rows={2}
            placeholder="Any advice or observations from the service technician..."
            value={formData.notes}
            onChange={(e) => handleChange('notes', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            icon={isEditing ? Save : Plus}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Saving...' : isEditing ? 'Update Record' : 'Save Maintenance Log'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
