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
  Eye,
  EyeOff,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
  FileSpreadsheet
} from 'lucide-react';
import Button from '../common/Button';
import Badge from '../common/Badge';
import Input from '../common/Input';
import { PRODUCT_CATEGORIES } from '../../data/categories';
import { ocrApi, ApiError } from '../../services/api';
import './ReceiptScannerModal.css';

export default function ReceiptScannerModal({ isOpen, onClose, onProductsSaved }) {
  const [step, setStep] = useState('upload'); // 'upload' | 'scanning' | 'review' | 'success'
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [candidateItems, setCandidateItems] = useState([]);
  const [attachDocument, setAttachDocument] = useState(true);
  const [showRawText, setShowRawText] = useState(false);
  const [activeItemIndex, setActiveItemIndex] = useState(0);

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
    setAttachDocument(true);
    setShowRawText(false);
    setActiveItemIndex(0);
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

    // Validate size
    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10 MB limit.');
      return;
    }

    setSelectedFile(file);
    setError(null);

    // Create preview if image
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = () => setFilePreview(reader.result);
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }

    // Automatically trigger scan
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
      setCandidateItems(
        response.items && response.items.length > 0
          ? response.items.map((item, idx) => ({
              ...item,
              tempId: `item_${idx}_${Date.now()}`,
              name: item.name || '',
              brand: item.brand || '',
              model: item.model || '',
              category: item.category || 'Other',
              purchaseDate: item.purchaseDate || new Date().toISOString().split('T')[0],
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
                name: 'Scanned Purchase',
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
            ]
      );
      setWarnings(response.warnings || []);
      setStep('review');
    } catch (err) {
      setError(err.message || 'Failed to analyze receipt. Please try another image or enter manually.');
      setStep('upload');
    } finally {
      setLoading(false);
    }
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
    setCandidateItems([...candidateItems, newItem]);
    setActiveItemIndex(candidateItems.length);
  };

  const handleRemoveItem = (index) => {
    if (candidateItems.length <= 1) return;
    const updated = candidateItems.filter((_, idx) => idx !== index);
    setCandidateItems(updated);
    if (activeItemIndex >= updated.length) {
      setActiveItemIndex(Math.max(0, updated.length - 1));
    }
  };

  const handleConfirmSave = async () => {
    // Validate that all items have a name
    for (let i = 0; i < candidateItems.length; i++) {
      if (!candidateItems[i].name.trim()) {
        setError(`Item #${i + 1} must have a valid product name.`);
        setActiveItemIndex(i);
        return;
      }
    }

    setLoading(true);
    setError(null);

    const payload = {
      items: candidateItems.map((it) => ({
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
        notes: it.notes ? it.notes.trim() : null
      })),
      tempFileToken: attachDocument && scanResult?.tempFileToken ? scanResult.tempFileToken : null,
      documentType: 'Purchase Bill'
    };

    try {
      const res = await ocrApi.confirm(payload);
      setSuccessCount(res.createdProducts?.length || candidateItems.length);
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

  const currentItem = candidateItems[activeItemIndex] || candidateItems[0];

  return (
    <div className="receipt-modal-backdrop" onClick={handleClose}>
      <div className="receipt-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="receipt-modal-header">
          <div className="receipt-header-info">
            <div className="receipt-badge-title">
              <Sparkles size={18} className="sparkle-icon" />
              <h3>Scan Receipt (AI & OCR)</h3>
            </div>
            <p>Extract, review, and confirm product details from bills & invoices</p>
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

          {/* STEP 1: UPLOAD & DROPZONE */}
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
                <h4>Upload or Drop Receipt File</h4>
                <p>Supports clear photos (JPG, PNG, WEBP) and multi-page PDF invoices</p>
                <span className="file-size-hint">Max file size: 10 MB</span>

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
                accept="image/jpeg,image/png,image/webp,application/pdf"
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

              {/* Tips for best OCR results */}
              <div className="ocr-tips-card">
                <div className="tips-title">
                  <ShieldCheck size={16} />
                  <span>Tips for 100% accurate scans</span>
                </div>
                <ul>
                  <li>Ensure good lighting without harsh glare or heavy shadows.</li>
                  <li>Flatten thermal receipts and keep all edges inside the camera frame.</li>
                  <li>Digital PDF invoices from Amazon, Flipkart, or Croma extract with instant high precision.</li>
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
              <h4>Analyzing Receipt with Tesseract OCR & PyMuPDF...</h4>
              <p className="scanning-sub">
                Detecting seller, line items, purchase dates, prices, and warranty terms...
              </p>
            </div>
          )}

          {/* STEP 3: REVIEW & CONFIRM WORKFLOW */}
          {step === 'review' && currentItem && (
            <div className="receipt-review-view">
              {/* Top Banner with Confidence & Guidance */}
              <div className="review-top-bar">
                <div className="confidence-pill-wrap">
                  <span className="confidence-label">Scan Confidence:</span>
                  {scanResult?.overallConfidenceLevel === 'high' && (
                    <Badge variant="success">
                      <CheckCircle2 size={13} style={{ marginRight: '4px' }} />
                      High Accuracy ({Math.round((scanResult?.overallConfidence || 0.85) * 100)}%)
                    </Badge>
                  )}
                  {scanResult?.overallConfidenceLevel === 'medium' && (
                    <Badge variant="warning">
                      <AlertTriangle size={13} style={{ marginRight: '4px' }} />
                      Medium Confidence ({Math.round((scanResult?.overallConfidence || 0.65) * 100)}%)
                    </Badge>
                  )}
                  {scanResult?.overallConfidenceLevel === 'low' && (
                    <Badge variant="danger">
                      <AlertCircle size={13} style={{ marginRight: '4px' }} />
                      Low Confidence ({Math.round((scanResult?.overallConfidence || 0.4) * 100)}%)
                    </Badge>
                  )}
                </div>

                <div className="review-bar-actions">
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

              {/* Warnings / Uncertainty Notices */}
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

              {/* Multi-Item Selector Tabs (if more than 1 item) */}
              <div className="item-tabs-header">
                <div className="tabs-list">
                  {candidateItems.map((item, idx) => (
                    <button
                      key={item.tempId}
                      className={`item-tab-btn ${activeItemIndex === idx ? 'active' : ''}`}
                      onClick={() => setActiveItemIndex(idx)}
                    >
                      <span>Item {idx + 1}: {item.name || 'Unnamed'}</span>
                      {candidateItems.length > 1 && (
                        <span
                          className="tab-delete-x"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveItem(idx);
                          }}
                          title="Remove item"
                        >
                          <X size={13} />
                        </span>
                      )}
                    </button>
                  ))}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Plus size={14} />}
                  onClick={handleAddItem}
                >
                  Add Another Item
                </Button>
              </div>

              {/* Form Editor for the Active Item */}
              <div className="review-form-grid">
                <div className="form-col-full">
                  <label className="field-label">
                    Product Name <span className="req">*</span>
                  </label>
                  <Input
                    placeholder="e.g. Apple iPhone 15 Pro 128GB"
                    value={currentItem.name}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'name', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Brand</label>
                  <Input
                    placeholder="e.g. Apple, Samsung, Sony"
                    value={currentItem.brand || ''}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'brand', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Model</label>
                  <Input
                    placeholder="e.g. A3101, XPS 9530"
                    value={currentItem.model || ''}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'model', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Category</label>
                  <select
                    className="custom-select-input"
                    value={currentItem.category}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'category', e.target.value)}
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
                    value={currentItem.purchaseDate || ''}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'purchaseDate', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Price (INR ₹)</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="e.g. 134900"
                    value={currentItem.price}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'price', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Quantity</label>
                  <Input
                    type="number"
                    min="1"
                    value={currentItem.quantity}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'quantity', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Seller / Retailer</label>
                  <Input
                    placeholder="e.g. Reliance Digital, Amazon, Croma"
                    value={currentItem.seller || ''}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'seller', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Serial Number</label>
                  <Input
                    placeholder="e.g. F2LL89J90X"
                    value={currentItem.serialNumber || ''}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'serialNumber', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">IMEI Number (Mobiles)</label>
                  <Input
                    placeholder="15-digit IMEI"
                    value={currentItem.imei || ''}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'imei', e.target.value)}
                  />
                </div>

                <div className="form-col">
                  <label className="field-label">Warranty / Notes</label>
                  <Input
                    placeholder="e.g. 1 Year Manufacturer Warranty"
                    value={currentItem.notes || ''}
                    onChange={(e) => handleFieldChange(activeItemIndex, 'notes', e.target.value)}
                  />
                </div>
              </div>

              {/* Auto Attach Document Checkbox */}
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

          {/* STEP 4: SUCCESS STATE */}
          {step === 'success' && (
            <div className="receipt-success-view">
              <div className="success-icon-wrap">
                <CheckCircle2 size={56} />
              </div>
              <h4>Receipt Successfully Processed!</h4>
              <p>
                Created <strong>{successCount}</strong> product{successCount > 1 ? 's' : ''} in your inventory
                {attachDocument ? ' and attached the receipt bill to documents.' : '.'}
              </p>
              <div className="success-actions">
                <Button variant="primary" onClick={handleClose}>
                  View Products
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
              <span>OCR candidates are editable. Products are only saved when you click Confirm.</span>
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
              >
                Confirm & Save {candidateItems.length > 1 ? `(${candidateItems.length} Items)` : 'Product'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
