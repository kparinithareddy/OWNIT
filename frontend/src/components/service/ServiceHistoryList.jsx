import React, { useState } from 'react';
import {
  Wrench,
  Calendar,
  Building,
  DollarSign,
  ShieldCheck,
  ShieldAlert,
  FileText,
  Edit2,
  Trash2,
  Plus,
  Hash,
  ExternalLink,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { servicesApi, documentsApi } from '../../services/api';
import './ServiceHistoryList.css';

export default function ServiceHistoryList({
  productId,
  productName,
  serviceRecords = [],
  onAddNew,
  onEdit,
  onRefresh
}) {
  const [deletingId, setDeletingId] = useState(null);
  const [actionError, setActionError] = useState(null);

  const handleDelete = async (record) => {
    if (!window.confirm(`Delete service record for "${record.problem}" on ${record.serviceDate}?`)) {
      return;
    }

    setDeletingId(record.id);
    setActionError(null);
    try {
      await servicesApi.delete(record.id);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Error deleting service record:', err);
      setActionError(err.message || 'Failed to delete service record.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleViewDoc = async (docId) => {
    try {
      const url = await documentsApi.viewFile(docId, false);
      window.open(url, '_blank');
    } catch (err) {
      console.error('Error viewing document:', err);
      alert('Could not open document file.');
    }
  };

  const totalSpent = serviceRecords.reduce((sum, r) => sum + (r.cost || 0), 0);
  const coveredCount = serviceRecords.filter(r => r.warrantyCovered).length;

  return (
    <div className="service-history-container">
      {/* Header & Metrics */}
      <div className="service-history-header-card">
        <div className="sh-header-left">
          <div className="sh-avatar-icon">
            <Wrench size={22} />
          </div>
          <div>
            <h3 className="sh-title">Service & Repair History</h3>
            <p className="sh-subtitle">
              Verified physical repairs, part replacements, and technician logs for <strong>{productName}</strong>
            </p>
          </div>
        </div>

        <div className="sh-header-actions">
          <Button variant="primary" icon={Plus} onClick={onAddNew}>
            Log Service Record
          </Button>
        </div>
      </div>

      {/* Summary Metrics Strip */}
      {serviceRecords.length > 0 && (
        <div className="service-metrics-strip">
          <div className="metric-chip">
            <span className="metric-label">Total Service Events</span>
            <span className="metric-value">{serviceRecords.length}</span>
          </div>
          <div className="metric-chip">
            <span className="metric-label">Warranty-Covered Repairs</span>
            <span className="metric-value green">{coveredCount}</span>
          </div>
          <div className="metric-chip">
            <span className="metric-label">Out-of-Pocket Cost</span>
            <span className="metric-value">₹{totalSpent.toLocaleString('en-IN')}</span>
          </div>
        </div>
      )}

      {actionError && (
        <div className="service-error-alert">
          <AlertCircle size={16} />
          <span>{actionError}</span>
        </div>
      )}

      {/* Service Records List */}
      {serviceRecords.length === 0 ? (
        <Card className="service-empty-card" padding="lg">
          <div className="service-empty-box">
            <div className="service-empty-icon">
              <Wrench size={32} />
            </div>
            <h4>No Service History Logged</h4>
            <p>
              Keep a verified record of repairs, screen swaps, battery replacements, and inspections to maintain your asset history and maximize Life Score.
            </p>
            <Button variant="primary" icon={Plus} onClick={onAddNew}>
              Log First Service Record
            </Button>
          </div>
        </Card>
      ) : (
        <div className="service-records-grid">
          {serviceRecords.map((rec) => (
            <Card key={rec.id} className="service-record-card" padding="md">
              {/* Card Header */}
              <div className="record-card-header">
                <div className="record-header-title-block">
                  <span className="record-date-badge">
                    <Calendar size={12} /> {rec.serviceDate}
                  </span>
                  {rec.warrantyCovered ? (
                    <span className="badge-covered">
                      <ShieldCheck size={12} /> Warranty Covered
                    </span>
                  ) : (
                    <span className="badge-paid">
                      <DollarSign size={12} /> Paid Service
                    </span>
                  )}
                </div>

                <div className="record-actions-row">
                  <button
                    className="record-btn-icon edit"
                    onClick={() => onEdit(rec)}
                    title="Edit service record"
                    aria-label="Edit record"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    className="record-btn-icon delete"
                    onClick={() => handleDelete(rec)}
                    disabled={deletingId === rec.id}
                    title="Delete service record"
                    aria-label="Delete record"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {/* Problem / Reason */}
              <div className="record-problem-row">
                <span className="record-section-label">Problem / Symptom:</span>
                <h4 className="record-problem-text">{rec.problem}</h4>
              </div>

              {/* Work Performed */}
              <div className="record-work-box">
                <span className="record-section-label">Work Performed:</span>
                <p className="record-work-text">{rec.workPerformed}</p>
              </div>

              {/* Metadata Grid (Provider, Cost, Document, Notes) */}
              <div className="record-meta-grid">
                <div className="meta-item">
                  <span className="meta-label">
                    <Building size={12} /> Service Center
                  </span>
                  <span className="meta-val">{rec.serviceCenter}</span>
                </div>

                <div className="meta-item">
                  <span className="meta-label">
                    <DollarSign size={12} /> Total Cost
                  </span>
                  <span className="meta-val">
                    {rec.cost > 0 ? `₹${rec.cost.toLocaleString('en-IN')}` : '₹0.00 (Covered)'}
                  </span>
                </div>

                {rec.documentId && (
                  <div className="meta-item">
                    <span className="meta-label">
                      <FileText size={12} /> Service Invoice
                    </span>
                    <button
                      className="doc-link-btn"
                      onClick={() => handleViewDoc(rec.documentId)}
                    >
                      <span>{rec.documentName || 'View Document'}</span>
                      <ExternalLink size={11} />
                    </button>
                  </div>
                )}

                {rec.notes && (
                  <div className="meta-item notes-item">
                    <span className="meta-label">
                      <Hash size={12} /> Reference Notes
                    </span>
                    <span className="meta-val notes">{rec.notes}</span>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
