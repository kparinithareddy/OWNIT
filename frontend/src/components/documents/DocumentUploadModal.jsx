import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, AlertCircle, CheckCircle2, X } from 'lucide-react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import { Select } from '../common/Input';
import { DOCUMENT_TYPE_OPTIONS } from '../../data/documentTypes';
import { productsApi, documentsApi, ApiError } from '../../services/api';

export default function DocumentUploadModal({
  isOpen,
  onClose,
  preselectedProductId = '',
  onSuccess
}) {
  const [products, setProducts] = useState([]);
  const [productId, setProductId] = useState(preselectedProductId || '');
  const [documentType, setDocumentType] = useState('Purchase Bill');
  const [selectedFile, setSelectedFile] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setProductId(preselectedProductId || '');
      setDocumentType('Purchase Bill');
      setSelectedFile(null);
      setErrorMessage('');

      // Fetch user products for dropdown
      productsApi.list()
        .then((data) => {
          setProducts(data);
          if (!preselectedProductId && data.length > 0) {
            setProductId(data[0].id);
          }
        })
        .catch((err) => {
          console.warn('Could not load products for document upload:', err);
        });
    }
  }, [isOpen, preselectedProductId]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check size limit (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage('File exceeds the 10 MB maximum limit. Please choose a smaller file.');
      setSelectedFile(null);
      return;
    }

    // Check extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    const allowed = ['.pdf', '.jpg', '.jpeg', '.png', '.webp', '.gif'];
    if (!allowed.includes(ext)) {
      setErrorMessage(`Invalid file format '${ext}'. Only PDF and image files (JPG, PNG, WEBP) are allowed.`);
      setSelectedFile(null);
      return;
    }

    setErrorMessage('');
    setSelectedFile(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!productId) {
      return setErrorMessage('Please select a product to associate with this document.');
    }

    if (!selectedFile) {
      return setErrorMessage('Please select a PDF or image file to upload.');
    }

    const formData = new FormData();
    formData.append('productId', productId);
    formData.append('documentType', documentType);
    formData.append('file', selectedFile);

    try {
      setIsUploading(true);
      const result = await documentsApi.upload(formData);
      if (onSuccess) onSuccess(result);
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to upload document. Please try again.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const productOptions = products.map((p) => ({
    value: p.id,
    label: `${p.name} (${p.brand} - ${p.category})`
  }));

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Upload Product Document"
      subtitle="Attach a purchase invoice, warranty card, or user manual"
      maxWidth="560px"
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

      {products.length === 0 && !preselectedProductId ? (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            You haven't added any products yet. Please add a product first before uploading documents.
          </p>
          <Button variant="primary" size="sm" onClick={onClose}>
            Got It
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <Select
            label="Select Associated Product"
            options={productOptions}
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            required
            disabled={isUploading || !!preselectedProductId}
          />

          <Select
            label="Document Type"
            options={DOCUMENT_TYPE_OPTIONS}
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            disabled={isUploading}
          />

          {/* File Picker Zone */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-main)', marginBottom: '6px' }}>
              Choose Document File (PDF, PNG, JPG, WEBP - Max 10MB) <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <div
              style={{
                border: '2px dashed var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                padding: '24px 16px',
                textAlign: 'center',
                backgroundColor: selectedFile ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onClick={() => document.getElementById('doc-file-input').click()}
            >
              <input
                id="doc-file-input"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp,.gif"
                onChange={handleFileChange}
                style={{ display: 'none' }}
                disabled={isUploading}
              />
              <UploadCloud size={32} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
              {selectedFile ? (
                <div>
                  <p style={{ fontWeight: 600, color: 'var(--primary)', fontSize: '0.9375rem' }}>
                    {selectedFile.name}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB &bull; Ready to upload
                  </p>
                </div>
              ) : (
                <div>
                  <p style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.875rem' }}>
                    Click to browse or drop file here
                  </p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Supported: PDF, JPG, PNG, WEBP (Up to 10 MB)
                  </p>
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--border-light)' }}>
            <Button variant="secondary" onClick={onClose} disabled={isUploading}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              icon={UploadCloud}
              loading={isUploading}
              disabled={isUploading || !selectedFile}
            >
              Upload & Save
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
