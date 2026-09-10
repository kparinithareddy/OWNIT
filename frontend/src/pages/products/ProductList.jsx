import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  Plus,
  Search,
  Calendar,
  DollarSign,
  Edit2,
  Trash2,
  Eye,
  Store,
  Hash,
  Smartphone,
  Laptop,
  Tv,
  Refrigerator,
  Volume2,
  Camera,
  Gamepad2,
  Sparkles,
  Layers
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import ProductFormModal from '../../components/products/ProductFormModal';
import { PRODUCT_CATEGORIES } from '../../data/categories';
import { productsApi } from '../../services/api';
import './ProductList.css';

// Helper to pick category icon
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

export default function ProductList() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  // Modals state
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [deletingProductId, setDeletingProductId] = useState(null);

  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await productsApi.list({
        category: selectedCategory,
        search: searchTerm
      });
      setProducts(data);
    } catch (err) {
      console.error('Error fetching products:', err);
      setError(err.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchTerm]);

  useEffect(() => {
    // Debounce search/filter fetch
    const timer = setTimeout(() => {
      fetchProducts();
    }, 200);
    return () => clearTimeout(timer);
  }, [fetchProducts]);

  const handleOpenAdd = () => {
    setEditingProduct(null);
    setIsFormModalOpen(true);
  };

  const handleOpenEdit = (e, product) => {
    e.stopPropagation();
    setEditingProduct(product);
    setIsFormModalOpen(true);
  };

  const handleDelete = async (e, productId, productName) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to permanently delete "${productName}"?`)) {
      return;
    }

    try {
      setDeletingProductId(productId);
      await productsApi.delete(productId);
      setProducts((prev) => prev.filter((p) => p.id !== productId));
    } catch (err) {
      alert(`Could not delete product: ${err.message}`);
    } finally {
      setDeletingProductId(null);
    }
  };

  const categories = ['All', ...PRODUCT_CATEGORIES];

  return (
    <PageContainer
      title="My Products & Assets"
      subtitle="Catalog, manage, and track all your physical items securely."
      actions={
        <Button
          variant="primary"
          icon={Plus}
          onClick={handleOpenAdd}
        >
          Add Product
        </Button>
      }
    >
      {/* Search & Category Filter Toolbar */}
      <div className="product-filter-bar">
        <div className="product-search-box">
          <Search size={16} className="product-search-icon" />
          <input
            type="text"
            placeholder="Search by product name, brand, model, serial #, or seller..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="product-search-input"
          />
        </div>

        <div className="product-filters">
          <div className="filter-group">
            <span className="filter-label"><Layers size={14} /> Category:</span>
            <div className="filter-pills">
              {categories.map((cat) => (
                <button
                  key={cat}
                  className={`filter-pill ${selectedCategory === cat ? 'filter-pill-active' : ''}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area: Loading / Error / Empty / Grid */}
      {loading && products.length === 0 ? (
        <LoadingState message="Loading your products..." description="Connecting to MongoDB..." />
      ) : error ? (
        <ErrorState
          title="Could not load products"
          description={error}
          onRetry={fetchProducts}
        />
      ) : products.length === 0 ? (
        <EmptyState
          title={searchTerm || selectedCategory !== 'All' ? 'No matching products found' : 'No products added yet'}
          description={
            searchTerm || selectedCategory !== 'All'
              ? 'Try clearing your search terms or selecting a different category filter.'
              : 'Get started by adding your first laptop, smartphone, or household appliance!'
          }
          actionLabel={searchTerm || selectedCategory !== 'All' ? 'Clear Filters' : 'Add First Product'}
          onAction={() => {
            if (searchTerm || selectedCategory !== 'All') {
              setSearchTerm('');
              setSelectedCategory('All');
            } else {
              handleOpenAdd();
            }
          }}
        />
      ) : (
        <div className="product-grid">
          {products.map((product) => {
            const IconComponent = getCategoryIcon(product.category);
            return (
              <Card
                key={product.id}
                hoverable
                className="product-card"
                onClick={() => navigate(`/products/${product.id}`)}
              >
                <div className="product-card-top">
                  <div className="product-avatar">
                    <IconComponent size={22} />
                  </div>
                  <Badge variant="info" size="sm">
                    {product.category}
                  </Badge>
                </div>

                <div className="product-card-info">
                  <span className="product-brand-tag">{product.brand}</span>
                  <h3 className="product-title">{product.name}</h3>
                  <p className="product-model">{product.model}</p>
                </div>

                <div className="product-card-meta">
                  <div className="product-meta-item">
                    <Calendar size={13} />
                    <span>Purchased: {product.purchaseDate}</span>
                  </div>
                  {product.seller && (
                    <div className="product-meta-item">
                      <Store size={13} />
                      <span>Store: {product.seller}</span>
                    </div>
                  )}
                  {product.serialNumber && (
                    <div className="product-meta-item">
                      <Hash size={13} />
                      <span>Serial: {product.serialNumber}</span>
                    </div>
                  )}
                </div>

                <div className="product-card-footer">
                  <div className="product-price">
                    ₹{product.price.toLocaleString('en-IN')}
                    {product.quantity > 1 && (
                      <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '4px' }}>
                        (Qty: {product.quantity})
                      </span>
                    )}
                  </div>

                  <div className="product-card-actions" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="card-icon-action-btn"
                      title="Edit Product"
                      onClick={(e) => handleOpenEdit(e, product)}
                    >
                      <Edit2 size={15} />
                    </button>
                    <button
                      className="card-icon-action-btn action-danger"
                      title="Delete Product"
                      disabled={deletingProductId === product.id}
                      onClick={(e) => handleDelete(e, product.id, product.name)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add / Edit Product Modal */}
      <ProductFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        initialProduct={editingProduct}
        onSuccess={() => {
          fetchProducts();
        }}
      />
    </PageContainer>
  );
}
