import React, { useState, useEffect } from 'react';
import {
  Package,
  Plus,
  Save,
  AlertCircle,
  Calendar,
  DollarSign,
  Hash,
  Store,
  RotateCcw,
  Sparkles,
  Info
} from 'lucide-react';
import Modal from '../common/Modal';
import Input, { Select } from '../common/Input';
import Button from '../common/Button';
import { CATEGORY_OPTIONS } from '../../data/categories';
import { RETURN_DURATION_PRESETS, VERIFIED_SELLER_DEFAULTS } from '../../data/sellerPolicies';
import { productsApi, ApiError } from '../../services/api';

function calculateClientReturnDeadline(startDateStr, durationStr) {
  if (!startDateStr || !durationStr || durationStr === 'None' || durationStr === 'No Returns') return '';
  const date = new Date(startDateStr);
  if (isNaN(date.getTime())) return '';

  const dur = durationStr.toLowerCase();
  const dayMatch = dur.match(/(\d+)\s*(?:day|d)/);
  const monthMatch = dur.match(/(\d+)\s*(?:month|mo|m)/);
  const weekMatch = dur.match(/(\d+)\s*(?:week|wk|w)/);

  let newDate = new Date(date);
  if (dayMatch) {
    const days = parseInt(dayMatch[1], 10);
    newDate.setDate(newDate.getDate() + days);
  } else if (weekMatch) {
    const weeks = parseInt(weekMatch[1], 10);
    newDate.setDate(newDate.getDate() + (weeks * 7));
  } else if (monthMatch) {
    const months = parseInt(monthMatch[1], 10);
    newDate.setMonth(newDate.getMonth() + months);
  } else {
    return '';
  }

  const y = newDate.getFullYear();
  const m = String(newDate.getMonth() + 1).padStart(2, '0');
  const d = String(newDate.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export default function ProductFormModal({
  isOpen,
  onClose,
  initialProduct = null,
  onSuccess
}) {
  const isEditing = !!initialProduct;

  const [formData, setFormData] = useState({
    name: '',
    brand: '',
    model: '',
    category: 'Mobile',
    purchaseDate: new Date().toISOString().split('T')[0],
    price: '',
    quantity: 1,
    seller: '',
    serialNumber: '',
    imei: '',
    image: '',
    notes: '',
    // Return / Replacement tracking
    returnDurationPreset: 'None',
    customReturnDuration: '',
    returnStartDate: '',
    returnDeadline: '',
    returnPolicySource: ''
  });

  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialProduct) {
      const isPreset = RETURN_DURATION_PRESETS.some(
        (p) => p.value === initialProduct.returnDuration
      );

      setFormData({
        name: initialProduct.name || '',
        brand: initialProduct.brand || '',
        model: initialProduct.model || '',
        category: initialProduct.category || 'Other',
        purchaseDate: initialProduct.purchaseDate || new Date().toISOString().split('T')[0],
        price: initialProduct.price !== undefined ? String(initialProduct.price) : '',
        quantity: initialProduct.quantity !== undefined ? initialProduct.quantity : 1,
        seller: initialProduct.seller || '',
        serialNumber: initialProduct.serialNumber || '',
        imei: initialProduct.imei || '',
        image: initialProduct.image || '',
        notes: initialProduct.notes || '',
        returnDurationPreset: initialProduct.returnDuration
          ? (isPreset ? initialProduct.returnDuration : 'Custom')
          : 'None',
        customReturnDuration: isPreset ? '' : (initialProduct.returnDuration || ''),
        returnStartDate: initialProduct.returnStartDate || initialProduct.purchaseDate || '',
        returnDeadline: initialProduct.returnDeadline || '',
        returnPolicySource: initialProduct.returnPolicySource || ''
      });
    } else {
      const todayStr = new Date().toISOString().split('T')[0];
      setFormData({
        name: '',
        brand: '',
        model: '',
        category: 'Mobile',
        purchaseDate: todayStr,
        price: '',
        quantity: 1,
        seller: '',
        serialNumber: '',
        imei: '',
        image: '',
        notes: '',
        returnDurationPreset: 'None',
        customReturnDuration: '',
        returnStartDate: todayStr,
        returnDeadline: '',
        returnPolicySource: ''
      });
    }
    setErrorMessage('');
  }, [initialProduct, isOpen]);

  const handleChange = (field, value) => {
    setFormData((prev) => {
      const updated = { ...prev, [field]: value };

      // Auto-detect verified seller defaults if seller changes and user hasn't set return duration
      if (field === 'seller' && value && prev.returnDurationPreset === 'None') {
        const verified = VERIFIED_SELLER_DEFAULTS[value.trim()];
        if (verified) {
          updated.returnDurationPreset = verified.duration;
          updated.returnPolicySource = verified.source;
          const start = updated.returnStartDate || updated.purchaseDate;
          updated.returnDeadline = calculateClientReturnDeadline(start, verified.duration);
        }
      }

      // Re-calculate return deadline if start date or purchase date changes
      if (field === 'purchaseDate' && (!prev.returnStartDate || prev.returnStartDate === prev.purchaseDate)) {
        updated.returnStartDate = value;
        const dur = prev.returnDurationPreset === 'Custom' ? prev.customReturnDuration : prev.returnDurationPreset;
        if (dur && dur !== 'None') {
          updated.returnDeadline = calculateClientReturnDeadline(value, dur);
        }
      }

      if (field === 'returnStartDate') {
        const dur = prev.returnDurationPreset === 'Custom' ? prev.customReturnDuration : prev.returnDurationPreset;
        if (dur && dur !== 'None') {
          updated.returnDeadline = calculateClientReturnDeadline(value, dur);
        }
      }

      return updated;
    });
  };

  const handleReturnPresetChange = (preset) => {
    setFormData((prev) => {
      const start = prev.returnStartDate || prev.purchaseDate;
      const effectiveDur = preset === 'Custom' ? prev.customReturnDuration : preset;
      const deadline = calculateClientReturnDeadline(start, effectiveDur);
      return {
        ...prev,
        returnDurationPreset: preset,
        returnDeadline: preset === 'None' || preset === 'No Returns' ? '' : deadline
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // Validation
    if (!formData.name.trim()) return setErrorMessage('Product name is required.');
    if (!formData.brand.trim()) return setErrorMessage('Brand is required.');
    if (!formData.model.trim()) return setErrorMessage('Model is required.');
    if (!formData.purchaseDate) return setErrorMessage('Purchase date is required.');
    if (formData.price === '' || isNaN(Number(formData.price)) || Number(formData.price) < 0) {
      return setErrorMessage('Please enter a valid price (₹).');
    }

    const effectiveReturnDuration =
      formData.returnDurationPreset === 'Custom'
        ? formData.customReturnDuration.trim()
        : formData.returnDurationPreset === 'None'
        ? null
        : formData.returnDurationPreset;

    const payload = {
      name: formData.name.trim(),
      brand: formData.brand.trim(),
      model: formData.model.trim(),
      category: formData.category,
      purchaseDate: formData.purchaseDate,
      price: parseFloat(formData.price),
      quantity: parseInt(formData.quantity, 10) || 1,
      seller: formData.seller.trim() || null,
      serialNumber: formData.serialNumber.trim() || null,
      imei: formData.imei.trim() || null,
      image: formData.image.trim() || null,
      notes: formData.notes.trim() || null,
      returnDuration: effectiveReturnDuration,
      returnStartDate: effectiveReturnDuration ? (formData.returnStartDate || formData.purchaseDate) : null,
      returnDeadline: effectiveReturnDuration ? (formData.returnDeadline || null) : null,
      returnPolicySource: formData.returnPolicySource.trim() || null
    };

    try {
      setIsSubmitting(true);
      let result;
      if (isEditing) {
        result = await productsApi.update(initialProduct.id, payload);
      } else {
        result = await productsApi.create(payload);
      }

      if (onSuccess) onSuccess(result);
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to save product. Please check your inputs and try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Edit Product' : 'Add New Product'}
      subtitle={isEditing ? 'Update the details for this physical asset' : 'Register a new product to your OWNIT inventory'}
      maxWidth="680px"
    >
      {errorMessage && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 14px',
          backgroundColor: 'var(--danger-light)',
          color: 'var(--danger)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.8125rem',
          marginBottom: '16px'
        }}>
          <AlertCircle size={16} style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Core Product Details */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          <Input
            label="Product Name"
            placeholder="e.g. iPhone 15 Pro"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            required
            disabled={isSubmitting}
          />

          <Input
            label="Brand"
            placeholder="e.g. Apple, Sony, Samsung"
            value={formData.brand}
            onChange={(e) => handleChange('brand', e.target.value)}
            required
            disabled={isSubmitting}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          <Input
            label="Model"
            placeholder="e.g. 256GB Black Titanium"
            value={formData.model}
            onChange={(e) => handleChange('model', e.target.value)}
            required
            disabled={isSubmitting}
          />

          <Select
            label="Category"
            options={CATEGORY_OPTIONS}
            value={formData.category}
            onChange={(e) => handleChange('category', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          <Input
            label="Purchase Date"
            type="date"
            icon={Calendar}
            value={formData.purchaseDate}
            onChange={(e) => handleChange('purchaseDate', e.target.value)}
            required
            disabled={isSubmitting}
          />

          <Input
            label="Price (₹)"
            type="number"
            step="0.01"
            min="0"
            icon={DollarSign}
            placeholder="e.g. 134900"
            value={formData.price}
            onChange={(e) => handleChange('price', e.target.value)}
            required
            disabled={isSubmitting}
          />

          <Input
            label="Quantity"
            type="number"
            min="1"
            placeholder="1"
            value={formData.quantity}
            onChange={(e) => handleChange('quantity', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          <Input
            label="Seller / Store"
            icon={Store}
            placeholder="e.g. Amazon India, Croma, Apple Store"
            value={formData.seller}
            onChange={(e) => handleChange('seller', e.target.value)}
            disabled={isSubmitting}
          />

          <Input
            label="Serial Number"
            icon={Hash}
            placeholder="e.g. F2LDF9012JK8"
            value={formData.serialNumber}
            onChange={(e) => handleChange('serialNumber', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        {/* Return & Replacement Policy Section */}
        <div style={{
          marginTop: '16px',
          marginBottom: '16px',
          padding: '14px 16px',
          background: 'var(--bg-surface-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-light)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: 'var(--text-main)', fontWeight: 600, fontSize: '0.875rem' }}>
            <RotateCcw size={16} color="var(--primary)" />
            <span>Return & Replacement Window</span>
            <span style={{ fontSize: '0.6875rem', fontWeight: 500, color: 'var(--text-muted)' }}>
              (Track return deadlines separately from warranty)
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '4px', color: 'var(--text-main)' }}>
                Return Window
              </label>
              <select
                value={formData.returnDurationPreset}
                onChange={(e) => handleReturnPresetChange(e.target.value)}
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
                <option value="None">None / Unknown Policy</option>
                {RETURN_DURATION_PRESETS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>

            {formData.returnDurationPreset === 'Custom' && (
              <Input
                label="Custom Duration"
                placeholder="e.g. 21 Days or 45 Days"
                value={formData.customReturnDuration}
                onChange={(e) => {
                  handleChange('customReturnDuration', e.target.value);
                  const start = formData.returnStartDate || formData.purchaseDate;
                  const dl = calculateClientReturnDeadline(start, e.target.value);
                  setFormData((prev) => ({ ...prev, returnDeadline: dl || prev.returnDeadline }));
                }}
              />
            )}

            {formData.returnDurationPreset !== 'None' && formData.returnDurationPreset !== 'No Returns' && (
              <>
                <Input
                  label="Return Start Date"
                  type="date"
                  value={formData.returnStartDate || formData.purchaseDate}
                  onChange={(e) => handleChange('returnStartDate', e.target.value)}
                />
                <Input
                  label="Return Deadline"
                  type="date"
                  value={formData.returnDeadline}
                  onChange={(e) => handleChange('returnDeadline', e.target.value)}
                />
              </>
            )}
          </div>

          {formData.returnDurationPreset !== 'None' && (
            <div style={{ marginTop: '10px' }}>
              <Input
                label="Policy Source / Remarks"
                placeholder="e.g. Amazon India Standard 7-Day Replacement Policy, Store Invoice"
                value={formData.returnPolicySource}
                onChange={(e) => handleChange('returnPolicySource', e.target.value)}
              />
            </div>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          <Input
            label="IMEI (Mobile Devices)"
            placeholder="e.g. 358921098234125"
            value={formData.imei}
            onChange={(e) => handleChange('imei', e.target.value)}
            disabled={isSubmitting}
          />

          <Input
            label="Image URL (Optional)"
            placeholder="https://example.com/image.jpg"
            value={formData.image}
            onChange={(e) => handleChange('image', e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-main)', marginBottom: '6px' }}>
            Notes / Warranty Remarks
          </label>
          <textarea
            rows={2}
            placeholder="Add any purchase details, warranty inclusions, or condition notes..."
            value={formData.notes}
            onChange={(e) => handleChange('notes', e.target.value)}
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-medium)',
              fontSize: '0.875rem',
              fontFamily: 'inherit',
              outline: 'none',
              backgroundColor: 'var(--bg-surface)'
            }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            icon={isEditing ? Save : Plus}
            disabled={isSubmitting}
          >
            {isSubmitting ? (isEditing ? 'Saving...' : 'Adding...') : (isEditing ? 'Save Changes' : 'Add Product')}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
