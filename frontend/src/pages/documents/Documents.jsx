import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  UploadCloud,
  Search,
  Filter,
  Download,
  Eye,
  Trash2,
  Package,
  Layers,
  FileCheck2,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import DocumentUploadModal from '../../components/documents/DocumentUploadModal';
import { DOCUMENT_TYPES } from '../../data/documentTypes';
import { documentsApi, productsApi } from '../../services/api';
import './Documents.css';

// Helper to format file sizes nicely
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Helper to pick thumbnail emoji / icon by type or MIME
function getDocVisual(mimeType, docType) {
  if (mimeType === 'application/pdf') return '📄';
  if (mimeType.startsWith('image/')) return '🖼️';
  if (docType === 'Warranty Card' || docType === 'Extended Warranty') return '🛡️';
  if (docType === 'User Manual') return '📘';
  return '📁';
}

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [selectedProduct, setSelectedProduct] = useState('All');

  // Modal
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [actionDocId, setActionDocId] = useState(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await documentsApi.list({
        productId: selectedProduct,
        documentType: selectedType
      });
      setDocuments(data);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError(err.message || 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  }, [selectedProduct, selectedType]);

  useEffect(() => {
    // Fetch products for dropdown filter
    productsApi.list().then(setProducts).catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDocuments();
    }, 150);
    return () => clearTimeout(timer);
  }, [fetchDocuments]);

  const handleView = async (doc) => {
    try {
      const objectUrl = await documentsApi.viewFile(doc.id, false);
      window.open(objectUrl, '_blank');
    } catch (err) {
      alert(`Could not view file: ${err.message}`);
    }
  };

  const handleDownload = async (doc) => {
    try {
      const objectUrl = await documentsApi.viewFile(doc.id, true);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = doc.originalFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err) {
      alert(`Could not download file: ${err.message}`);
    }
  };

  const handleDelete = async (docId, docTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${docTitle}"?`)) return;

    try {
      setActionDocId(docId);
      await documentsApi.delete(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    } finally {
      setActionDocId(null);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      doc.originalFilename.toLowerCase().includes(term) ||
      (doc.productName && doc.productName.toLowerCase().includes(term)) ||
      (doc.productBrand && doc.productBrand.toLowerCase().includes(term)) ||
      doc.documentType.toLowerCase().includes(term)
    );
  });

  const docTypes = ['All', ...DOCUMENT_TYPES];

  return (
    <PageContainer
      title="Document Vault"
      subtitle="Safely store, organize, and view your purchase bills, warranty cards, and user manuals."
      actions={
        <Button
          variant="primary"
          icon={UploadCloud}
          onClick={() => setIsUploadModalOpen(true)}
        >
          Upload Document
        </Button>
      }
    >
      {/* OCR & Upload Dropzone Banner */}
      <Card className="doc-upload-dropzone" onClick={() => setIsUploadModalOpen(true)}>
        <div className="upload-dropzone-content">
          <div className="upload-icon-circle">
            <UploadCloud size={28} />
          </div>
          <h4 className="upload-dropzone-title">Attach Bills, Warranties & Manuals</h4>
          <p className="upload-dropzone-subtitle">
            Upload PDF invoices or image receipts up to 10 MB. Documents are securely linked to your products and isolated to your account.
          </p>
          <Button variant="outline" size="sm" style={{ marginTop: '12px' }}>
            Choose File to Upload
          </Button>
        </div>
      </Card>

      {/* Filter and Search Bar */}
      <div className="doc-search-bar-container">
        <div className="doc-search-box">
          <Search size={16} className="doc-search-icon" />
          <input
            type="text"
            placeholder="Search documents by filename, product name, or document type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="doc-search-input"
          />
        </div>

        <div className="doc-filter-controls">
          {/* Document Type Filter */}
          <div className="doc-filter-group">
            <span className="doc-filter-label"><FileText size={13} /> Type:</span>
            <div className="doc-pills-row">
              {docTypes.map((type) => (
                <button
                  key={type}
                  className={`doc-filter-pill ${selectedType === type ? 'pill-active' : ''}`}
                  onClick={() => setSelectedType(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Product Filter Dropdown */}
          {products.length > 0 && (
            <div className="doc-filter-group">
              <span className="doc-filter-label"><Package size={13} /> Product:</span>
              <select
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
                className="doc-select"
              >
                <option value="All">All Products</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      {loading && documents.length === 0 ? (
        <LoadingState message="Loading documents..." description="Fetching vault records..." />
      ) : error ? (
        <ErrorState
          title="Could not load documents"
          description={error}
          onRetry={fetchDocuments}
        />
      ) : documents.length === 0 ? (
        <EmptyState
          title={selectedType !== 'All' || selectedProduct !== 'All' ? 'No matching documents' : 'No documents uploaded yet'}
          description={
            selectedType !== 'All' || selectedProduct !== 'All'
              ? 'Try changing or clearing your filters.'
              : 'Upload your first purchase receipt, warranty card, or user guide to keep records safe.'
          }
          actionLabel={selectedType !== 'All' || selectedProduct !== 'All' ? 'Reset Filters' : 'Upload First Document'}
          onAction={() => {
            if (selectedType !== 'All' || selectedProduct !== 'All') {
              setSelectedType('All');
              setSelectedProduct('All');
              setSearchTerm('');
            } else {
              setIsUploadModalOpen(true);
            }
          }}
        />
      ) : filteredDocs.length === 0 ? (
        <EmptyState
          title="No documents match your search"
          description="Try adjusting your search query."
          actionLabel="Clear Search"
          onAction={() => setSearchTerm('')}
        />
      ) : (
        <div className="documents-grid">
          {filteredDocs.map((doc) => (
            <Card key={doc.id} className="doc-card" padding="md">
              <div className="doc-card-top">
                <span className="doc-thumbnail-emoji">{getDocVisual(doc.mimeType, doc.documentType)}</span>
                <Badge variant="info" size="sm">
                  {doc.documentType}
                </Badge>
              </div>

              <div className="doc-card-body">
                <h4 className="doc-card-title" title={doc.originalFilename}>
                  {doc.originalFilename}
                </h4>
                <p className="doc-product-link">
                  Linked Product:{' '}
                  <strong>{doc.productName || 'Registered Asset'}</strong>
                </p>
              </div>

              <div className="doc-card-footer">
                <span className="doc-meta-info">
                  {formatFileSize(doc.fileSize)} &bull; {new Date(doc.uploadedAt).toLocaleDateString()}
                </span>
                <div className="doc-actions">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Eye}
                    title="View / Preview in Browser"
                    onClick={() => handleView(doc)}
                  >
                    View
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Download}
                    title="Download File"
                    onClick={() => handleDownload(doc)}
                  >
                    Download
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Trash2}
                    className="doc-delete-btn"
                    title="Delete Document"
                    disabled={actionDocId === doc.id}
                    onClick={() => handleDelete(doc.id, doc.originalFilename)}
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSuccess={() => {
          fetchDocuments();
        }}
      />
    </PageContainer>
  );
}
