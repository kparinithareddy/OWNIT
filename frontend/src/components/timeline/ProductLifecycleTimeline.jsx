import React, { useState, useEffect, useMemo } from 'react';
import {
  Package,
  ShoppingCart,
  RotateCcw,
  ShieldCheck,
  ShieldAlert,
  FileText,
  Bell,
  Wrench,
  Clock,
  Calendar,
  Plus,
  ArrowDownUp,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Info,
  DollarSign
} from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import Badge from '../common/Badge';
import Modal from '../common/Modal';
import Input from '../common/Input';
import LoadingState from '../common/LoadingState';
import { productsApi } from '../../services/api';
import './ProductLifecycleTimeline.css';

function getEventIcon(eventType, category) {
  switch (eventType) {
    case 'PURCHASE':
      return ShoppingCart;
    case 'RETURN_WINDOW_START':
    case 'RETURN_WINDOW_END':
      return RotateCcw;
    case 'WARRANTY_START':
      return ShieldCheck;
    case 'WARRANTY_EXPIRY':
      return ShieldAlert;
    case 'DOCUMENT_ATTACHED':
      return FileText;
    case 'NOTIFICATION_ALERT':
      return Bell;
    case 'SERVICE':
    case 'MAINTENANCE':
    case 'REPAIR':
      return Wrench;
    default:
      if (category === 'warranty') return ShieldCheck;
      if (category === 'return') return RotateCcw;
      if (category === 'service' || category === 'maintenance') return Wrench;
      if (category === 'document') return FileText;
      return Clock;
  }
}

function getStatusBadge(status) {
  switch (status) {
    case 'completed':
      return { variant: 'neutral', label: 'Completed' };
    case 'active':
      return { variant: 'active', label: 'Active Window' };
    case 'critical':
      return { variant: 'warning', label: 'Ending Soon' };
    case 'upcoming':
      return { variant: 'info', label: 'Upcoming' };
    default:
      return { variant: 'neutral', label: 'Recorded' };
  }
}

export default function ProductLifecycleTimeline({ productId, productName }) {
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sorting & Filtering
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc' (Oldest first) | 'desc' (Newest first)
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Custom event modal state
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [logFormData, setLogFormData] = useState({
    eventType: 'SERVICE',
    title: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    category: 'service',
    status: 'completed',
    cost: '',
    provider: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const fetchTimeline = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await productsApi.getTimeline(productId);
      setTimelineData(data);
    } catch (err) {
      console.error('Error fetching product timeline:', err);
      setError(err.message || 'Failed to load lifecycle timeline.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      fetchTimeline();
    }
  }, [productId]);

  const handleAddEvent = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!logFormData.title.trim()) {
      return setFormError('Event title is required.');
    }
    if (!logFormData.date) {
      return setFormError('Event date is required.');
    }

    try {
      setIsSubmitting(true);
      const payload = {
        eventType: logFormData.eventType,
        title: logFormData.title.trim(),
        description: logFormData.description.trim(),
        date: logFormData.date,
        category: logFormData.category,
        status: logFormData.status,
        icon: 'wrench',
        metadata: {
          cost: logFormData.cost ? parseFloat(logFormData.cost) : null,
          provider: logFormData.provider.trim() || null
        }
      };

      await productsApi.addTimelineEvent(productId, payload);
      setIsLogModalOpen(false);
      setLogFormData({
        eventType: 'SERVICE',
        title: '',
        description: '',
        date: new Date().toISOString().split('T')[0],
        category: 'service',
        status: 'completed',
        cost: '',
        provider: ''
      });
      fetchTimeline();
    } catch (err) {
      setFormError(err.message || 'Failed to save lifecycle event.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter and sort events
  const displayedEvents = useMemo(() => {
    if (!timelineData || !timelineData.events) return [];
    let list = [...timelineData.events];

    if (selectedCategory !== 'all') {
      list = list.filter((item) => item.category === selectedCategory);
    }

    list.sort((a, b) => {
      const dateA = new Date(a.date.slice(0, 10)).getTime();
      const dateB = new Date(b.date.slice(0, 10)).getTime();
      return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    });

    return list;
  }, [timelineData, selectedCategory, sortOrder]);

  if (loading) {
    return <LoadingState message="Loading lifecycle timeline..." description="Synthesizing chronological events..." />;
  }

  if (error) {
    return (
      <Card>
        <div style={{ padding: '20px', color: 'var(--danger)' }}>
          {error}
          <div style={{ marginTop: '10px' }}>
            <Button variant="outline" size="sm" onClick={fetchTimeline}>
              Retry
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="lifecycle-timeline-wrap">
      {/* Timeline Controls & Filter Toolbar */}
      <div className="timeline-toolbar">
        <div className="timeline-filters-group">
          <button
            className={`timeline-filter-chip ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            All Milestones ({timelineData?.totalEvents || 0})
          </button>
          <button
            className={`timeline-filter-chip ${selectedCategory === 'purchase' || selectedCategory === 'return' ? 'active' : ''}`}
            onClick={() => setSelectedCategory(selectedCategory === 'purchase' ? 'all' : 'purchase')}
          >
            Purchase & Returns
          </button>
          <button
            className={`timeline-filter-chip ${selectedCategory === 'warranty' ? 'active' : ''}`}
            onClick={() => setSelectedCategory(selectedCategory === 'warranty' ? 'all' : 'warranty')}
          >
            Warranties
          </button>
          <button
            className={`timeline-filter-chip ${selectedCategory === 'service' || selectedCategory === 'maintenance' ? 'active' : ''}`}
            onClick={() => setSelectedCategory(selectedCategory === 'service' ? 'all' : 'service')}
          >
            Service & Maintenance
          </button>
          <button
            className={`timeline-filter-chip ${selectedCategory === 'document' ? 'active' : ''}`}
            onClick={() => setSelectedCategory(selectedCategory === 'document' ? 'all' : 'document')}
          >
            Documents
          </button>
        </div>

        <div className="timeline-actions-group">
          <Button
            variant="ghost"
            size="sm"
            icon={ArrowDownUp}
            onClick={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
          >
            {sortOrder === 'asc' ? 'Oldest First' : 'Newest First'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            icon={Plus}
            onClick={() => setIsLogModalOpen(true)}
          >
            Log Service / Maintenance
          </Button>
        </div>
      </div>

      {/* Timeline List */}
      {displayedEvents.length === 0 ? (
        <Card>
          <div className="timeline-empty-box">
            <Clock size={36} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-main)' }}>
              No lifecycle events in this filter
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: '4px 0 14px' }}>
              Select "All Milestones" or log a new service or repair milestone.
            </p>
            <Button variant="outline" size="sm" onClick={() => setSelectedCategory('all')}>
              Show All Events
            </Button>
          </div>
        </Card>
      ) : (
        <div className="timeline-stream">
          {displayedEvents.map((evt, idx) => {
            const IconComp = getEventIcon(evt.eventType, evt.category);
            const statusInfo = getStatusBadge(evt.status);
            const isLast = idx === displayedEvents.length - 1;

            return (
              <div key={evt.id} className={`timeline-node ${evt.category} ${evt.status}`}>
                {/* Visual Node Line & Icon */}
                <div className="timeline-axis">
                  <div className={`timeline-icon-bubble ${evt.category}`}>
                    <IconComp size={16} />
                  </div>
                  {!isLast && <div className="timeline-connector-line" />}
                </div>

                {/* Event Card Content */}
                <div className="timeline-card">
                  <div className="timeline-card-header">
                    <div className="timeline-header-left">
                      <span className="timeline-date-tag">
                        <Calendar size={12} /> {evt.date}
                      </span>
                      <h4 className="timeline-event-title">{evt.title}</h4>
                    </div>

                    <div className="timeline-header-right">
                      <Badge variant={statusInfo.variant} size="sm">
                        {statusInfo.label}
                      </Badge>
                    </div>
                  </div>

                  <p className="timeline-event-desc">{evt.description}</p>

                  {/* Metadata Chips if available */}
                  {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                    <div className="timeline-meta-chips">
                      {evt.metadata.price !== undefined && evt.metadata.price !== null && (
                        <span className="meta-chip">
                          ₹{Number(evt.metadata.price).toLocaleString('en-IN')}
                        </span>
                      )}
                      {evt.metadata.seller && (
                        <span className="meta-chip">Store: {evt.metadata.seller}</span>
                      )}
                      {evt.metadata.provider && (
                        <span className="meta-chip">Provider: {evt.metadata.provider}</span>
                      )}
                      {evt.metadata.duration && (
                        <span className="meta-chip">Duration: {evt.metadata.duration}</span>
                      )}
                      {evt.metadata.cost !== undefined && evt.metadata.cost !== null && (
                        <span className="meta-chip">Cost: ₹{evt.metadata.cost}</span>
                      )}
                      {evt.metadata.documentType && (
                        <span className="meta-chip">Type: {evt.metadata.documentType}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Log Custom Service/Maintenance Event Modal */}
      <Modal
        isOpen={isLogModalOpen}
        onClose={() => setIsLogModalOpen(false)}
        title="Log Lifecycle / Service Milestone"
        subtitle={`Record maintenance, repairs, or service events for ${productName || 'this product'}`}
        maxWidth="560px"
      >
        {formError && (
          <div style={{ padding: '10px 14px', background: 'var(--danger-light)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem', marginBottom: '14px' }}>
            {formError}
          </div>
        )}

        <form onSubmit={handleAddEvent}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '4px', color: 'var(--text-main)' }}>
                Milestone Category
              </label>
              <select
                value={logFormData.eventType}
                onChange={(e) => {
                  const val = e.target.value;
                  setLogFormData((prev) => ({
                    ...prev,
                    eventType: val,
                    category: val === 'SERVICE' ? 'service' : val === 'MAINTENANCE' ? 'maintenance' : 'other'
                  }));
                }}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-medium)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-main)',
                  fontSize: '0.8125rem'
                }}
              >
                <option value="SERVICE">Routine Servicing</option>
                <option value="MAINTENANCE">Preventive Maintenance</option>
                <option value="REPAIR">Repair / Component Replacement</option>
                <option value="CUSTOM">Custom Milestone</option>
              </select>
            </div>

            <Input
              label="Event Date"
              type="date"
              value={logFormData.date}
              onChange={(e) => setLogFormData({ ...logFormData, date: e.target.value })}
              required
            />
          </div>

          <div style={{ marginTop: '12px' }}>
            <Input
              label="Event Title"
              placeholder="e.g. Annual AC Filter Cleaning & Gas Refill"
              value={logFormData.title}
              onChange={(e) => setLogFormData({ ...logFormData, title: e.target.value })}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '12px' }}>
            <Input
              label="Service Center / Technician"
              placeholder="e.g. Official Samsung Service, Urban Company"
              value={logFormData.provider}
              onChange={(e) => setLogFormData({ ...logFormData, provider: e.target.value })}
            />

            <Input
              label="Cost / Expense (₹)"
              type="number"
              placeholder="e.g. 1499"
              value={logFormData.cost}
              onChange={(e) => setLogFormData({ ...logFormData, cost: e.target.value })}
            />
          </div>

          <div style={{ marginTop: '12px', marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '4px', color: 'var(--text-main)' }}>
              Description & Work Done
            </label>
            <textarea
              rows={3}
              placeholder="Notes on parts replaced, diagnostic findings, or maintenance checks performed..."
              value={logFormData.description}
              onChange={(e) => setLogFormData({ ...logFormData, description: e.target.value })}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-medium)',
                background: 'var(--bg-surface)',
                color: 'var(--text-main)',
                fontSize: '0.8125rem',
                fontFamily: 'inherit'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '14px', borderTop: '1px solid var(--border-light)' }}>
            <Button variant="secondary" onClick={() => setIsLogModalOpen(false)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" icon={Plus} disabled={isSubmitting}>
              {isSubmitting ? 'Logging...' : 'Add to Timeline'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
