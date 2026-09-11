import React, { useState, useRef } from 'react';
import {
  X,
  Upload,
  Camera,
  FileText,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Plus,
  Trash2,
  Edit3,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  Sparkles,
  ShieldCheck,
  HelpCircle,
  CheckSquare,
  Square,
  Package,
  Calendar,
  DollarSign,
  Store,
  Hash,
  Tag
} from 'lucide-react';
import Button from '../common/Button';
import Badge from '../common/Badge';
import Input from '../common/Input';
import { PRODUCT_CATEGORIES } from '../../data/categories';
import { ocrApi } from '../../services/api';
import './ReceiptScannerModal.css';

export default function ReceiptScannerModal({ isOpen, onClose, onProductsSaved }) {
  const [step, setStep] = useState('upload'); // 'upload' | 'scanning' | 'review' | 'success'
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [candidateItems, setCandidateItems] = useState([]);
  const [editingIndex, setEditingIndex] = useState(null);
  const [attachDocument, setAttachDocument] = useState(true);
  const [showRawText, setShowRawText] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [successCount, setSuccessCount] = useState(0);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  if (!isOpen) return null;

  const resetState = () => {
    setStep('upload');
    setSelectedFile(null);
    setFilePreview(null);
    setScanResult(null);
    setCandidateItems([]);
    setEditingIndex(null);
    setAttachDocument(true);
    setShowRawText(false);
    setError(null);
    setWarnings([]);
    setSuccessCount(0);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10 MB limit.');
      return;
    }

    setSelectedFile(file);
    setError(null);

    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = () => setFilePreview(reader.result);
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }

    processReceiptScan(file);
  };

  const processReceiptScan = async (file) => {
    setStep('scanning');
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await ocrApi.scan(formData);
      setScanResult(response);

      const items = (response.items && response.items.length > 0)
        ? response.items.map((item, idx) => ({
            ...item,
            tempId: `item_${idx}_${Date.now()}`,
            selected: true, // Selected by default for user confirmation
            name: item.name || '',
            brand: item.brand || '',
            model: item.model || '',
            category: item.category || 'Other',
            purchaseDate: item.purchaseDate || response.invoiceDate || new Date().toISOString().split('T')[0],
            price: item.price !== null && item.price !== undefined ? item.price : '',
            quantity: item.quantity || 1,
            seller: item.seller || response.seller || '',
            serialNumber: item.serialNumber || '',
            imei: item.imei || '',
            notes: item.warrantyInfo ? `Warranty: ${item.warrantyInfo}` : ''
          }))
        : [
            {
              tempId: `item_0_${Date.now()}`,
              selected: true,
              name: 'Detected Product',
              brand: '',
              model: '',
              category: 'Other',
              purchaseDate: response.invoiceDate || new Date().toISOString().split('T')[0],
              price: response.totalAmount || '',
              quantity: 1,
              seller: response.seller || '',
              serialNumber: '',
              imei: '',
              notes: '',
              confidenceLevel: 'medium',
              uncertainFields: ['name', 'category']
            }
          ];

      setCandidateItems(items);
      setWarnings(response.warnings || []);
      setStep('review');
    } catch (err) {
      setError(err.message || 'Failed to analyze receipt. Please try another image or enter manually.');
      setStep('upload');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (index) => {
    setCandidateItems((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        selected: !updated[index].selected
      };
      return updated;
    });
  };

  const toggleSelectAll = () => {
    const allSelected = candidateItems.every((it) => it.selected);
    setCandidateItems((prev) =>
      prev.map((it) => ({
        ...it,
        selected: !allSelected
      }))
    );
  };

  const handleFieldChange = (index, field, value) => {
    setCandidateItems((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [field]: value
      };
      return updated;
    });
  };

  const handleAddItem = () => {
    const newItem = {
      tempId: `item_${candidateItems.length}_${Date.now()}`,
      selected: true,
      name: '',
      brand: '',
      model: '',
      category: 'Other',
      purchaseDate: scanResult?.invoiceDate || new Date().toISOString().split('T')[0],
      price: '',
      quantity: 1,
      seller: scanResult?.seller || '',
      serialNumber: '',
      imei: '',
      notes: '',
      confidenceLevel: 'high',
      uncertainFields: []
    };
    const nextList = [...candidateItems, newItem];
    setCandidateItems(nextList);
    setEditingIndex(nextList.length - 1);
  };

  const handleRemoveItem = (index) => {
    if (candidateItems.length <= 1) {
      // If only 1 item left, uncheck instead of removing
      setCandidateItems((prev) => {
        const updated = [...prev];
        updated[0].selected = false;
        return updated;
      });
      return;
    }
    setCandidateItems((prev) => prev.filter((_, idx) => idx !== index));
    if (editingIndex === index) {
      setEditingIndex(null);
    } else if (editingIndex > index) {
      setEditingIndex(editingIndex - 1);
    }
  };

  const handleConfirmSave = async () => {
    const selectedItems = candidateItems.filter((it) => it.selected);
    if (selectedItems.length === 0) {
      setError('Please select at least one product to save to your inventory.');
      return;
    }

    // Validate valid names
    for (let i = 0; i < selectedItems.length; i++) {
      if (!selectedItems[i].name.trim()) {
        setError(`Product #${i + 1} must have a valid product name.`);
        return;
      }
    }

    setLoading(true);
    setError(null);

    const payload = {
      items: selectedItems.map((it) => ({
        name: it.name.trim(),
        brand: it.brand ? it.brand.trim() : null,
        model: it.model ? it.model.trim() : null,
        category: it.category || 'Other',
        purchaseDate: it.purchaseDate || null,
        price: it.price !== '' && it.price !== null ? parseFloat(it.price) : null,
        quantity: parseInt(it.quantity, 10) || 1,
        seller: it.seller ? it.seller.trim() : null,
        serialNumber: it.serialNumber ? it.serialNumber.trim() : null,
        imei: it.imei ? it.imei.trim() : null,
        notes: it.notes ? it.notes.trim() : null,
        warrantyInfo: it.warrantyInfo || null,
        warrantyDuration: it.warrantyDuration || null,
        warrantyType: it.warrantyType || null,
        warrantyStartDate: it.warrantyStartDate || null,
        warrantyExpiryDate: it.warrantyExpiryDate || null,
        warrantyBenefits: it.warrantyBenefits || null,
        warrantyExclusions: it.warrantyExclusions || null,
        warrantyProvider: it.warrantyProvider || null,
        warrantyServiceInfo: it.warrantyServiceInfo || null
      })),
      tempFileToken: attachDocument && scanResult?.tempFileToken ? scanResult.tempFileToken : null,
      documentType: 'Purchase Bill'
    };

    try {
      const res = await ocrApi.confirm(payload);
      setSuccessCount(res.createdProducts?.length || selectedItems.length);
      setStep('success');
      if (onProductsSaved) {
        onProductsSaved(res.createdProducts);
      }
    } catch (err) {
      setError(err.message || 'Failed to save confirmed products to your inventory.');
    } finally {
      setLoading(false);
    }
  };

  const selectedCount = candidateItems.filter((it) => it.selected).length;

  return (
    <div className="receipt-modal-backdrop" onClick={handleClose}>
      <div className="receipt-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="receipt-modal-header">
          <div className="receipt-header-info">
            <div className="receipt-badge-title">
              <Sparkles size={18} className="sparkle-icon" />
              <h3>Scan Receipt & Extract Products</h3>
            </div>
            <p>Accurately extract multiple items, models, and prices with review & confirmation</p>
          </div>
          <button className="receipt-close-btn" onClick={handleClose}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="receipt-modal-body">
          {error && (
            <div className="receipt-error-banner">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {/* STEP 1: UPLOAD VIEW */}
          {step === 'upload' && (
            <div className="receipt-upload-view">
              <div
                className="receipt-dropzone"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files?.[0]) {
                    handleFileSelect({ target: { files: e.dataTransfer.files } });
                  }
                }}
              >
                <div className="dropzone-icon-wrap">
                  <Upload size={36} />
                </div>
                <h4>Upload Receipt or Invoice</h4>
                <p>Supports photos (JPG, PNG, WEBP), multi-page PDF, and Word documents (.docx)</p>
                <span className="file-size-hint">Extracts multiple products in a single bill • 100% offline & secure</span>

                <div className="receipt-action-buttons" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="primary"
                    icon={<FileText size={16} />}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Select File
                  </Button>
                  <Button
                    variant="secondary"
                    icon={<Camera size={16} />}
                    onClick={() => cameraInputRef.current?.click()}
                  >
                    Take Photo
                  </Button>
                </div>
              </div>

              {/* Hidden file inputs */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,application/pdf,.docx,.doc,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />

              <div className="ocr-tips-card">
                <div className="tips-title">
                  <ShieldCheck size={16} />
                  <span>How multi-product extraction works</span>
                </div>
                <ul>
                  <li>Invoices with multiple items (e.g. TV, Fridge, Headphones) are parsed into individual products.</li>
                  <li>You can review, edit, uncheck, or remove any item before saving.</li>
                  <li>Nothing is saved to your account until you review and click <strong>Confirm & Save</strong>.</li>
                </ul>
              </div>
            </div>
          )}

          {/* STEP 2: SCANNING ANIMATION */}
          {step === 'scanning' && (
            <div className="receipt-scanning-view">
              <div className="scanner-animation-box">
                <div className="scanner-document">
                  <FileText size={56} className="doc-icon" />
                  <div className="scanner-laser"></div>
                </div>
              </div>
              <h4>Analyzing Receipt with OCR Pipeline...</h4>
              <p className="scanning-sub">
                Segmenting products, detecting brands, models, quantities, and purchase amounts...
              </p>
            </div>
          )}

          {/* STEP 3: CONFIRMATION UI - DETECTED PRODUCTS LIST */}
          {step === 'review' && (
            <div className="receipt-review-view">
              {/* Review Bar & Quick Controls */}
              <div className="review-top-bar">
                <div className="detected-products-header">
                  <h4 className="detected-title">
                    Detected Products ({selectedCount} of {candidateItems.length} selected)
                  </h4>
                  <p className="detected-sub">
                    Select the products you want to add. Click <strong>Edit</strong> to modify details.
                  </p>
                </div>

                <div className="review-bar-actions">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Plus size={14} />}
                    onClick={handleAddItem}
                  >
                    Add Product
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<RefreshCw size={14} />}
                    onClick={() => {
                      setStep('upload');
                      setSelectedFile(null);
                    }}
                  >
                    Scan Again
                  </Button>
                </div>
              </div>

              {/* Warnings / Uncertainty banner */}
              {warnings.length > 0 && (
                <div className="review-warnings-box">
                  <AlertTriangle size={16} />
                  <div>
                    {warnings.map((w, idx) => (
                      <p key={idx}>{w}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Multi-Product Candidate Cards */}
              <div className="detected-products-list">
                {candidateItems.map((item, idx) => {
                  const isEditing = editingIndex === idx;
                  return (
                    <div
                      key={item.tempId}
                      className={`detected-product-card ${item.selected ? 'is-selected' : 'is-unselected'}`}
                    >
                      {/* Card Summary Header */}
                      <div className="card-top-row">
                        <div className="card-check-and-name">
                          <button
                            type="button"
                            className="checkbox-btn"
                            onClick={() => toggleSelect(idx)}
                            title={item.selected ? 'Deselect product' : 'Select product'}
                          >
                            {item.selected ? (
                              <CheckSquare size={20} className="check-icon checked" />
                            ) : (
                              <Square size={20} className="check-icon unchecked" />
                            )}
                          </button>

                          <div className="product-title-badge-group">
                            <span className="product-name-heading">
                              {item.name || 'Unnamed Product'}
                            </span>
                            <Badge variant="primary">{item.category || 'Other'}</Badge>
                            {item.brand && <Badge variant="neutral">{item.brand}</Badge>}
                          </div>
                        </div>

                        <div className="card-action-btns">
                          <button
                            type="button"
                            className={`action-btn-pill ${isEditing ? 'active' : ''}`}
                            onClick={() => setEditingIndex(isEditing ? null : idx)}
                          >
                            <Edit3 size={14} />
                            <span>{isEditing ? 'Done' : 'Edit'}</span>
                          </button>
                          <button
                            type="button"
                            className="action-btn-pill danger"
                            onClick={() => handleRemoveItem(idx)}
                            title="Remove candidate"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>

                      {/* Compact Attributes Preview (When Not Editing) */}
                      {!isEditing && (
                        <div className="card-meta-summary">
                          {item.brand && (
                            <div className="meta-pill">
                              <span className="meta-k">Brand:</span>
                              <span className="meta-v">{item.brand}</span>
                            </div>
                          )}
                          {item.model && (
                            <div className="meta-pill">
                              <span className="meta-k">Model:</span>
                              <span className="meta-v">{item.model}</span>
                            </div>
                          )}
                          {item.price !== '' && item.price !== null && (
                            <div className="meta-pill price-pill">
                              <span className="meta-k">Price:</span>
                              <span className="meta-v">₹{Number(item.price).toLocaleString('en-IN')}</span>
                            </div>
                          )}
                          {item.quantity > 1 && (
                            <div className="meta-pill">
                              <span className="meta-k">Qty:</span>
                              <span className="meta-v">{item.quantity}</span>
                            </div>
                          )}
                          {item.purchaseDate && (
                            <div className="meta-pill">
                              <span className="meta-k">Date:</span>
                              <span className="meta-v">{item.purchaseDate}</span>
                            </div>
                          )}
                          {item.seller && (
                            <div className="meta-pill">
                              <span className="meta-k">Seller:</span>
                              <span className="meta-v">{item.seller}</span>
                            </div>
                          )}
                          {item.serialNumber && (
                            <div className="meta-pill">
                              <span className="meta-k">S/N:</span>
                              <span className="meta-v">{item.serialNumber}</span>
                            </div>
                          )}
                          {(item.warrantyInfo || item.warrantyDuration) && (
                            <div className="meta-pill" style={{ backgroundColor: '#ecfdf5', borderColor: '#a7f3d0', color: '#065f46' }}>
                              <span className="meta-k" style={{ color: '#047857', fontWeight: 600 }}>🛡️ Warranty:</span>
                              <span className="meta-v" style={{ fontWeight: 600 }}>
                                {item.warrantyInfo || `${item.warrantyDuration || '1 Year'} ${item.warrantyType || 'Manufacturer Warranty'}`}
                              </span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Full Form Editor (When Editing) */}
                      {isEditing && (
                        <div className="card-edit-form">
                          <div className="edit-form-grid">
                            <div className="form-col-full">
                              <label className="field-label">
                                Product Name <span className="req">*</span>
                              </label>
                              <Input
                                placeholder="e.g. Samsung TV"
                                value={item.name}
                                onChange={(e) => handleFieldChange(idx, 'name', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Brand</label>
                              <Input
                                placeholder="e.g. Samsung, LG, Sony"
                                value={item.brand || ''}
                                onChange={(e) => handleFieldChange(idx, 'brand', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Model</label>
                              <Input
                                placeholder="e.g. UA55DU8000, GL-S292RDSX"
                                value={item.model || ''}
                                onChange={(e) => handleFieldChange(idx, 'model', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Category</label>
                              <select
                                className="custom-select-input"
                                value={item.category}
                                onChange={(e) => handleFieldChange(idx, 'category', e.target.value)}
                              >
                                {PRODUCT_CATEGORIES.map((cat) => (
                                  <option key={cat} value={cat}>
                                    {cat}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div className="form-col">
                              <label className="field-label">Purchase Date</label>
                              <Input
                                type="date"
                                value={item.purchaseDate || ''}
                                onChange={(e) => handleFieldChange(idx, 'purchaseDate', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Price (INR ₹)</label>
                              <Input
                                type="number"
                                step="0.01"
                                placeholder="e.g. 54990"
                                value={item.price}
                                onChange={(e) => handleFieldChange(idx, 'price', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Quantity</label>
                              <Input
                                type="number"
                                min="1"
                                value={item.quantity}
                                onChange={(e) => handleFieldChange(idx, 'quantity', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Seller / Store</label>
                              <Input
                                placeholder="e.g. Reliance Digital, Amazon"
                                value={item.seller || ''}
                                onChange={(e) => handleFieldChange(idx, 'seller', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Serial Number</label>
                              <Input
                                placeholder="e.g. 99482XJ"
                                value={item.serialNumber || ''}
                                onChange={(e) => handleFieldChange(idx, 'serialNumber', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">IMEI Number</label>
                              <Input
                                placeholder="15-digit IMEI (for mobiles)"
                                value={item.imei || ''}
                                onChange={(e) => handleFieldChange(idx, 'imei', e.target.value)}
                              />
                            </div>

                            <div className="form-col">
                              <label className="field-label">Warranty / Notes</label>
                              <Input
                                placeholder="e.g. 1 Year Manufacturer Warranty"
                                value={item.notes || ''}
                                onChange={(e) => handleFieldChange(idx, 'notes', e.target.value)}
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Attach Document Checkbox */}
              <div className="attach-receipt-check">
                <label className="checkbox-container">
                  <input
                    type="checkbox"
                    checked={attachDocument}
                    onChange={(e) => setAttachDocument(e.target.checked)}
                  />
                  <span className="checkbox-text">
                    📎 Attach this receipt file as a <strong>Purchase Bill</strong> document to the created products
                  </span>
                </label>
              </div>

              {/* Raw OCR Text Disclosure */}
              <div className="raw-text-drawer">
                <button
                  type="button"
                  className="raw-text-toggle-btn"
                  onClick={() => setShowRawText(!showRawText)}
                >
                  {showRawText ? <EyeOff size={15} /> : <Eye size={15} />}
                  <span>{showRawText ? 'Hide Raw OCR Text' : 'View Raw OCR Text (Audit & Debug)'}</span>
                </button>
                {showRawText && (
                  <pre className="raw-text-content">
                    {scanResult?.rawText || 'No text extracted.'}
                  </pre>
                )}
              </div>
            </div>
          )}

          {/* STEP 4: SUCCESS VIEW */}
          {step === 'success' && (
            <div className="receipt-success-view">
              <div className="success-icon-wrap">
                <CheckCircle2 size={56} />
              </div>
              <h4>Products Successfully Saved!</h4>
              <p>
                Created <strong>{successCount}</strong> product{successCount > 1 ? 's' : ''} in your inventory
                {attachDocument ? ' and attached the receipt bill to documents.' : '.'}
              </p>
              <div className="success-actions">
                <Button variant="primary" onClick={handleClose}>
                  View Inventory
                </Button>
                <Button
                  variant="outline"
                  icon={<RefreshCw size={15} />}
                  onClick={resetState}
                >
                  Scan Another Receipt
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        {step === 'review' && (
          <div className="receipt-modal-footer">
            <div className="footer-notice">
              <HelpCircle size={14} />
              <span>Only checked products [✓] will be saved to your inventory.</span>
            </div>
            <div className="footer-actions">
              <Button variant="ghost" onClick={handleClose} disabled={loading}>
                Cancel
              </Button>
              <Button
                variant="primary"
                icon={<CheckCircle2 size={16} />}
                onClick={handleConfirmSave}
                loading={loading}
                disabled={selectedCount === 0}
              >
                Confirm & Save {selectedCount > 0 ? `(${selectedCount} Product${selectedCount > 1 ? 's' : ''})` : ''}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
