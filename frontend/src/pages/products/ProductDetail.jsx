import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Package,
  Calendar,
  DollarSign,
  Store,
  Hash,
  FileText,
  Bot,
  ArrowLeft,
  Edit2,
  Trash2,
  Clock,
  Layers,
  Smartphone,
  Laptop,
  Tv,
  Refrigerator,
  Volume2,
  Camera,
  Gamepad2,
  Sparkles,
  Info
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import ErrorState from '../../components/common/ErrorState';
import ProductFormModal from '../../components/products/ProductFormModal';
import { productsApi } from '../../services/api';
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

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchProduct = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await productsApi.get(id);
      setProduct(data);
    } catch (err) {
      console.error('Error fetching product:', err);
      setError(err.message || 'Product not found or access denied.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProduct();
  }, [fetchProduct]);

  const handleDelete = async () => {
    if (!product) return;
    if (!window.confirm(`Are you sure you want to permanently delete "${product.name}"?`)) {
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

  if (loading) {
    return (
      <PageContainer>
        <LoadingState message="Loading product details..." description="Fetching asset information from MongoDB..." />
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
            icon={Edit2}
            onClick={() => setIsEditModalOpen(true)}
          >
            Edit Product
          </Button>
          <Button
            variant="danger"
            icon={Trash2}
            disabled={isDeleting}
            onClick={handleDelete}
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

      {/* Notes & Assistant Teaser */}
      {product.notes && (
        <Card title="Notes & Maintenance Specifications">
          <p style={{ fontSize: '0.875rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
            {product.notes}
          </p>
        </Card>
      )}

      {/* Edit Modal */}
      <ProductFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        initialProduct={product}
        onSuccess={(updated) => {
          setProduct(updated);
        }}
      />
    </PageContainer>
  );
}
