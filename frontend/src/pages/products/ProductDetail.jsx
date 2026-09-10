import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Package,
  Calendar,
  DollarSign,
  Store,
  Hash,
  FileText,
  UploadCloud,
  Eye,
  Download,
  Trash2,
  ArrowLeft,
  Edit2,
  Clock,
  Layers,
  Smartphone,
  Laptop,
  Tv,
  Refrigerator,
  Volume2,
  Camera,
  Gamepad2,
  Sparkles
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import ErrorState from '../../components/common/ErrorState';
import ProductFormModal from '../../components/products/ProductFormModal';
import DocumentUploadModal from '../../components/documents/DocumentUploadModal';
import { productsApi, documentsApi } from '../../services/api';
import './ProductDetail.css';

function getCategoryIcon(cat) {
  switch (cat) {
    case 'Mobile': return Smartphone;
    case 'Laptop': return Laptop;
    case 'TV': return Tv;
    case 'Refrigerator': return Refrigerator;
    case 'Audio': return Volume2;
    case 'Camera': return Camera;
    case 'Gaming': return Gamepad2;
    case 'Home Appliance':
    case 'Air Conditioner':
    case 'Washing Machine': return Sparkles;
    default: return Package;
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isUploadDocModalOpen, setIsUploadDocModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchProductAndDocs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [prodData, docsData] = await Promise.all([
        productsApi.get(id),
        documentsApi.list({ productId: id })
      ]);
      setProduct(prodData);
      setDocuments(docsData);
    } catch (err) {
      console.error('Error fetching product & docs:', err);
      setError(err.message || 'Product not found or access denied.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProductAndDocs();
  }, [fetchProductAndDocs]);

  const handleDeleteProduct = async () => {
    if (!product) return;
    if (!window.confirm(`Are you sure you want to permanently delete "${product.name}"? This will also remove associated documents.`)) {
      return;
    }

    try {
      setIsDeleting(true);
      await productsApi.delete(product.id);
      navigate('/products', { replace: true });
    } catch (err) {
      alert(`Failed to delete product: ${err.message}`);
      setIsDeleting(false);
    }
  };

  const handleViewDoc = async (doc) => {
    try {
      const objectUrl = await documentsApi.viewFile(doc.id, false);
      window.open(objectUrl, '_blank');
    } catch (err) {
      alert(`Could not view file: ${err.message}`);
    }
  };

  const handleDownloadDoc = async (doc) => {
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

  const handleDeleteDoc = async (docId, docName) => {
    if (!window.confirm(`Delete document "${docName}"?`)) return;
    try {
      await documentsApi.delete(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <PageContainer>
        <LoadingState message="Loading product details..." description="Fetching asset and document information..." />
      </PageContainer>
    );
  }

  if (error || !product) {
    return (
      <PageContainer>
        <ErrorState
          title="Product Not Found"
          description={error || 'The requested product does not exist or you do not have permission to view it.'}
          onRetry={() => navigate('/products')}
          retryLabel="Back to Products"
        />
      </PageContainer>
    );
  }

  const IconComponent = getCategoryIcon(product.category);

  return (
    <PageContainer
      badge={
        <Link to="/products" className="back-link">
          <ArrowLeft size={14} /> Back to Products
        </Link>
      }
      title={product.name}
      subtitle={`${product.brand} • Model: ${product.model}`}
      actions={
        <div className="product-detail-actions">
          <Button
            variant="outline"
            icon={UploadCloud}
            onClick={() => setIsUploadDocModalOpen(true)}
          >
            Attach Document
          </Button>
          <Button
            variant="outline"
            icon={Edit2}
            onClick={() => setIsEditModalOpen(true)}
          >
            Edit
          </Button>
          <Button
            variant="danger"
            icon={Trash2}
            disabled={isDeleting}
            onClick={handleDeleteProduct}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      }
    >
      {/* Hero Overview Card */}
      <Card className="product-hero-card" padding="lg">
        <div className="hero-grid">
          <div className="hero-left">
            <div className="hero-avatar">
              <IconComponent size={36} />
            </div>
            <div className="hero-info">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <Badge variant="info" size="sm">
                  {product.category}
                </Badge>
                <span className="hero-brand">{product.brand}</span>
              </div>
              <h2 className="hero-title">{product.name}</h2>
              <p className="hero-model">{product.model}</p>
              {product.notes && <p className="hero-desc">{product.notes}</p>}
            </div>
          </div>

          <div className="hero-right">
            <div className="price-tag-card">
              <span className="price-tag-label">Total Value</span>
              <span className="price-tag-value">₹{product.price.toLocaleString('en-IN')}</span>
              {product.quantity > 1 && (
                <span className="price-tag-qty">Quantity: {product.quantity}</span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* 2-Column Detail Grid */}
      <div className="tab-grid-2col">
        {/* Purchase & Seller Info */}
        <Card title="Purchase & Vendor Details">
          <div className="detail-meta-list">
            <div className="detail-meta-row">
              <span className="meta-label"><Calendar size={15} /> Purchase Date:</span>
              <span className="meta-val">{product.purchaseDate}</span>
            </div>
            <div className="detail-meta-row">
              <span className="meta-label"><DollarSign size={15} /> Unit Price:</span>
              <span className="meta-val">₹{product.price.toLocaleString('en-IN')}</span>
            </div>
            <div className="detail-meta-row">
              <span className="meta-label"><Store size={15} /> Store / Vendor:</span>
              <span className="meta-val">{product.seller || 'Not specified'}</span>
            </div>
            <div className="detail-meta-row">
              <span className="meta-label"><Package size={15} /> Quantity:</span>
              <span className="meta-val">{product.quantity} unit(s)</span>
            </div>
          </div>
        </Card>

        {/* Identifiers & Hardware Info */}
        <Card title="Device Identifiers">
          <div className="detail-meta-list">
            <div className="detail-meta-row">
              <span className="meta-label"><Hash size={15} /> Serial Number:</span>
              <span className="meta-val">{product.serialNumber || 'Not recorded'}</span>
            </div>
            <div className="detail-meta-row">
              <span className="meta-label"><Smartphone size={15} /> IMEI Number:</span>
              <span className="meta-val">{product.imei || 'N/A'}</span>
            </div>
            <div className="detail-meta-row">
              <span className="meta-label"><Layers size={15} /> Category:</span>
              <span className="meta-val">{product.category}</span>
            </div>
            <div className="detail-meta-row">
              <span className="meta-label"><Clock size={15} /> Registered On:</span>
              <span className="meta-val">{new Date(product.createdAt).toLocaleDateString()}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Attached Documents Section */}
      <Card
        title={`Attached Documents (${documents.length})`}
        subtitle="Purchase invoices, warranty certificates, and manuals linked to this asset"
        action={
          <Button
            variant="outline"
            size="sm"
            icon={UploadCloud}
            onClick={() => setIsUploadDocModalOpen(true)}
          >
            Attach Document
          </Button>
        }
      >
        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px 16px' }}>
            <FileText size={32} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-main)' }}>
              No documents attached to this product
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '4px', marginBottom: '16px' }}>
              Upload your purchase bill or warranty card to keep safe records for warranty claims.
            </p>
            <Button
              variant="primary"
              size="sm"
              icon={UploadCloud}
              onClick={() => setIsUploadDocModalOpen(true)}
            >
              Upload Document Now
            </Button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {documents.map((doc) => (
              <div
                key={doc.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-surface-secondary)',
                  border: '1px solid var(--border-light)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '1.5rem' }}>
                    {doc.mimeType === 'application/pdf' ? '📄' : '🖼️'}
                  </span>
                  <div>
                    <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      {doc.originalFilename}
                    </h5>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {doc.documentType} &bull; {formatFileSize(doc.fileSize)} &bull; {new Date(doc.uploadedAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Button variant="ghost" size="sm" icon={Eye} onClick={() => handleViewDoc(doc)}>
                    View
                  </Button>
                  <Button variant="ghost" size="sm" icon={Download} onClick={() => handleDownloadDoc(doc)}>
                    Download
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Trash2}
                    style={{ color: 'var(--danger)' }}
                    onClick={() => handleDeleteDoc(doc.id, doc.originalFilename)}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Edit Product Modal */}
      <ProductFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        initialProduct={product}
        onSuccess={(updated) => {
          setProduct(updated);
        }}
      />

      {/* Upload Document Modal */}
      <DocumentUploadModal
        isOpen={isUploadDocModalOpen}
        onClose={() => setIsUploadDocModalOpen(false)}
        preselectedProductId={product.id}
        onSuccess={() => {
          fetchProductAndDocs();
        }}
      />
    </PageContainer>
  );
}
