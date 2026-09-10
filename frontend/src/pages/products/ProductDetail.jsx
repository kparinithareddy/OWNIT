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
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Smartphone,
  Laptop,
  Tv,
  Refrigerator,
  Volume2,
  Camera,
  Gamepad2,
  Sparkles,
  Plus,
  PhoneCall,
  CheckCircle2,
  XCircle,
  HelpCircle
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import ErrorState from '../../components/common/ErrorState';
import ProductFormModal from '../../components/products/ProductFormModal';
import DocumentUploadModal from '../../components/documents/DocumentUploadModal';
import WarrantyFormModal from '../../components/warranty/WarrantyFormModal';
import { productsApi, documentsApi, warrantiesApi } from '../../services/api';
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
  const [warranties, setWarranties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active tab: 'overview' | 'warranties' | 'documents'
  const [activeTab, setActiveTab] = useState('overview');

  // Modals state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isUploadDocModalOpen, setIsUploadDocModalOpen] = useState(false);
  const [isWarrantyModalOpen, setIsWarrantyModalOpen] = useState(false);
  const [selectedWarranty, setSelectedWarranty] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchProductData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [prodData, docsData, warrantiesData] = await Promise.all([
        productsApi.get(id),
        documentsApi.list({ productId: id }),
        warrantiesApi.getByProduct(id)
      ]);
      setProduct(prodData);
      setDocuments(docsData);
      setWarranties(warrantiesData);
    } catch (err) {
      console.error('Error fetching product details:', err);
      setError(err.message || 'Product not found or access denied.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProductData();
  }, [fetchProductData]);

  const handleDeleteProduct = async () => {
    if (!product) return;
    if (!window.confirm(`Are you sure you want to permanently delete "${product.name}"? This will also remove associated documents and warranty records.`)) {
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

  const handleDeleteWarranty = async (warrantyId, typeName) => {
    if (!window.confirm(`Delete "${typeName}" component?`)) return;
    try {
      await warrantiesApi.delete(warrantyId);
      setWarranties((prev) => prev.filter((w) => w.id !== warrantyId));
    } catch (err) {
      alert(`Failed to delete warranty: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <PageContainer>
        <LoadingState message="Loading product details..." description="Fetching asset, warranty, and document data..." />
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

  // Derive top warranty status badge for hero
  const activeWarrantiesCount = warranties.filter((w) => w.status === 'Active').length;
  const expiringWarrantiesCount = warranties.filter((w) => w.status === 'Expiring Soon').length;

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
            icon={ShieldCheck}
            onClick={() => {
              setSelectedWarranty(null);
              setIsWarrantyModalOpen(true);
            }}
          >
            + Add Warranty
          </Button>
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
                <Badge variant="info" size="sm">
                  {product.category}
                </Badge>
                <span className="hero-brand">{product.brand}</span>
                {warranties.length > 0 ? (
                  expiringWarrantiesCount > 0 ? (
                    <Badge variant="warning" size="sm" dot>
                      {expiringWarrantiesCount} Expiring Soon
                    </Badge>
                  ) : activeWarrantiesCount > 0 ? (
                    <Badge variant="active" size="sm" dot>
                      {activeWarrantiesCount} Active Component(s)
                    </Badge>
                  ) : (
                    <Badge variant="danger" size="sm" dot>
                      Warranties Expired
                    </Badge>
                  )
                ) : (
                  <Badge variant="neutral" size="sm">
                    No Warranty Added
                  </Badge>
                )}
              </div>
              <h2 className="hero-title">{product.name}</h2>
              <p className="hero-model">{product.model}</p>
              {product.notes && <p className="hero-desc">{product.notes}</p>}
            </div>
          </div>

          <div className="hero-right">
            <div className="price-tag-card">
              <span className="price-tag-label">Total Asset Value</span>
              <span className="price-tag-value">₹{product.price.toLocaleString('en-IN')}</span>
              {product.quantity > 1 && (
                <span className="price-tag-qty">Quantity: {product.quantity}</span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Navigation Tab Bar */}
      <div className="product-tab-bar">
        <button
          className={`product-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Layers size={16} /> Asset Overview
        </button>
        <button
          className={`product-tab-btn ${activeTab === 'warranties' ? 'active' : ''}`}
          onClick={() => setActiveTab('warranties')}
        >
          <ShieldCheck size={16} /> Warranty Components ({warranties.length})
        </button>
        <button
          className={`product-tab-btn ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          <FileText size={16} /> Attached Documents ({documents.length})
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
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
      )}

      {/* TAB 2: WARRANTIES */}
      {activeTab === 'warranties' && (
        <Card
          title={`Warranty Components (${warranties.length})`}
          subtitle="Comprehensive, Panel, Motor, Extended, or Accidental Damage coverage components"
          action={
            <Button
              variant="primary"
              size="sm"
              icon={Plus}
              onClick={() => {
                setSelectedWarranty(null);
                setIsWarrantyModalOpen(true);
              }}
            >
              Add Component
            </Button>
          }
        >
          {warranties.length === 0 ? (
            <div className="tab-empty-state">
              <ShieldCheck size={36} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
              <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>
                No warranty components tracked yet
              </h4>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '6px auto 16px' }}>
                Products often come with multiple coverage tiers (e.g. 2-Year Comprehensive + 5-Year Panel/Compressor). Add your components to monitor expiration dates.
              </p>
              <Button
                variant="primary"
                size="sm"
                icon={Plus}
                onClick={() => {
                  setSelectedWarranty(null);
                  setIsWarrantyModalOpen(true);
                }}
              >
                Add First Warranty Component
              </Button>
            </div>
          ) : (
            <div className="warranty-components-grid">
              {warranties.map((w) => {
                const isExpiring = w.status === 'Expiring Soon';
                const isExpired = w.status === 'Expired';
                const statusBadge = isExpiring
                  ? 'warning'
                  : isExpired
                  ? 'danger'
                  : 'active';

                return (
                  <div key={w.id} className={`warranty-component-card ${w.status.toLowerCase().replace(' ', '-')}`}>
                    <div className="w-comp-header">
                      <div className="w-comp-title-row">
                        <ShieldCheck
                          size={22}
                          className={`w-comp-icon ${statusBadge}`}
                        />
                        <div>
                          <h4 className="w-comp-name">{w.type}</h4>
                          <span className="w-comp-provider">Provider: <strong>{w.provider}</strong></span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Badge variant={statusBadge} size="sm" dot>
                          {w.status}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Edit2}
                          onClick={() => {
                            setSelectedWarranty(w);
                            setIsWarrantyModalOpen(true);
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Trash2}
                          style={{ color: 'var(--danger)' }}
                          onClick={() => handleDeleteWarranty(w.id, w.type)}
                        />
                      </div>
                    </div>

                    {/* Timeline & Countdown info */}
                    <div className="w-comp-timeline">
                      <div className="w-time-item">
                        <span className="w-time-label">Duration</span>
                        <span className="w-time-val">{w.duration}</span>
                      </div>
                      <div className="w-time-item">
                        <span className="w-time-label">Start Date</span>
                        <span className="w-time-val">{w.startDate}</span>
                      </div>
                      <div className="w-time-item">
                        <span className="w-time-label">Expiry Date</span>
                        <span className="w-time-val expiry">{w.expiryDate || 'N/A'}</span>
                      </div>
                      <div className="w-time-item">
                        <span className="w-time-label">Status</span>
                        <span className="w-time-val days-left">
                          {w.daysRemaining < 0
                            ? `Expired ${Math.abs(w.daysRemaining)} days ago`
                            : w.daysRemaining === 0
                            ? 'Expires Today'
                            : `${w.daysRemaining} days remaining`}
                        </span>
                      </div>
                    </div>

                    {/* Benefits & Inclusions */}
                    {w.benefits && w.benefits.length > 0 && (
                      <div className="w-comp-details-section">
                        <span className="w-details-title">Covered Inclusions:</span>
                        <div className="w-tags-row">
                          {w.benefits.map((b, idx) => (
                            <span key={idx} className="w-benefit-chip">✓ {b}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Exclusions */}
                    {w.exclusions && w.exclusions.length > 0 && (
                      <div className="w-comp-details-section">
                        <span className="w-details-title">Exclusions:</span>
                        <div className="w-tags-row">
                          {w.exclusions.map((ex, idx) => (
                            <span key={idx} className="w-exclusion-chip">✕ {ex}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Claim Procedure & Contacts */}
                    {(w.claimProcedure || w.serviceInformation) && (
                      <div className="w-comp-claim-box">
                        {w.claimProcedure && (
                          <p className="w-claim-text">
                            <strong>Claim Procedure:</strong> {w.claimProcedure}
                          </p>
                        )}
                        {w.serviceInformation && (
                          <p className="w-claim-text" style={{ marginTop: '4px' }}>
                            <strong><PhoneCall size={12} /> Contact / Support:</strong> {w.serviceInformation}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      )}

      {/* TAB 3: ATTACHED DOCUMENTS */}
      {activeTab === 'documents' && (
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
            <div className="tab-empty-state">
              <FileText size={36} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
              <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>
                No documents attached to this product
              </h4>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: '6px auto 16px', maxWidth: '400px' }}>
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
      )}

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
          fetchProductData();
        }}
      />

      {/* Add / Edit Warranty Modal */}
      <WarrantyFormModal
        isOpen={isWarrantyModalOpen}
        onClose={() => setIsWarrantyModalOpen(false)}
        productId={product.id}
        productName={product.name}
        initialWarranty={selectedWarranty}
        onSuccess={() => {
          fetchProductData();
        }}
      />
    </PageContainer>
  );
}
