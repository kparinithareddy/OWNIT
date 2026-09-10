import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Sparkles,
  Camera,
  Plus,
  ArrowRight,
  Search,
  Filter,
  Layers,
  Store,
  Calendar,
  AlertCircle,
  FileText,
  Smartphone,
  Laptop,
  Tv,
  Refrigerator,
  Volume2,
  Camera as CameraIcon,
  Gamepad2,
  Tag
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card, { StatCard } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import ProductFormModal from '../../components/products/ProductFormModal';
import Modal from '../../components/common/Modal';
import { PRODUCT_CATEGORIES } from '../../data/categories';
import { productsApi } from '../../services/api';
import './Dashboard.css';

// Helper to pick category icon
function getCategoryIcon(cat) {
  switch (cat) {
    case 'Mobile': return Smartphone;
    case 'Laptop': return Laptop;
    case 'TV': return Tv;
    case 'Refrigerator': return Refrigerator;
    case 'Audio': return Volume2;
    case 'Camera': return CameraIcon;
    case 'Gaming': return Gamepad2;
    case 'Home Appliance':
    case 'Air Conditioner':
    case 'Washing Machine': return Sparkles;
    default: return Package;
  }
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search and filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedBrand, setSelectedBrand] = useState('All');

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await productsApi.list();
      setProducts(data);
    } catch (err) {
      console.error('Error fetching dashboard products:', err);
      setError(err.message || 'Failed to connect to backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  // Compute unique brands from current user's products
  const availableBrands = useMemo(() => {
    const brands = new Set();
    products.forEach((p) => {
      if (p.brand && p.brand.trim()) {
        brands.add(p.brand.trim());
      }
    });
    return ['All', ...Array.from(brands).sort()];
  }, [products]);

  // Filter products client-side for immediate responsive search/brand/category filtering
  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      const matchesSearch =
        !searchTerm.trim() ||
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.brand.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (p.serialNumber && p.serialNumber.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (p.seller && p.seller.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesCategory =
        selectedCategory === 'All' || p.category === selectedCategory;

      const matchesBrand =
        selectedBrand === 'All' || p.brand.toLowerCase() === selectedBrand.toLowerCase();

      return matchesSearch && matchesCategory && matchesBrand;
    });
  }, [products, searchTerm, selectedCategory, selectedBrand]);

  const totalValue = products.reduce(
    (acc, p) => acc + (p.price * (p.quantity || 1)),
    0
  );

  return (
    <PageContainer
      title="Dashboard Overview"
      subtitle="Track your physical assets, active warranties, and upcoming expiration deadlines."
      actions={
        <div className="dashboard-top-actions">
          <Button
            variant="outline"
            icon={Camera}
            onClick={() => setIsScanModalOpen(true)}
          >
            Scan Receipt (OCR)
          </Button>
          <Button
            variant="primary"
            icon={Plus}
            onClick={() => setIsAddModalOpen(true)}
          >
            Add Product
          </Button>
        </div>
      }
    >
      {/* 1. Summary Cards (4 Cards) */}
      <div className="dashboard-stats-grid">
        <StatCard
          title="Total Products"
          value={loading ? '...' : String(products.length)}
          subtitle={products.length > 0 ? `Total Value: ₹${totalValue.toLocaleString('en-IN')}` : 'No products yet'}
          icon={Package}
          variant="primary"
        />
        <StatCard
          title="Active Warranties"
          value={loading ? '...' : '0'}
          subtitle="🟢 Active (Pending Warranty Sync)"
          icon={ShieldCheck}
          variant="success"
        />
        <StatCard
          title="Expiring Soon"
          value="0"
          subtitle="🟠 Expiring within 30 days"
          icon={Clock}
          variant="warning"
        />
        <StatCard
          title="Expired"
          value="0"
          subtitle="🔴 Out of coverage"
          icon={ShieldAlert}
          variant="danger"
        />
      </div>

      {/* 2. Expiring Soon Section */}
      <Card
        title="⏳ Expiring Soon (Warranties & Returns)"
        subtitle="Monitors deadlines requiring attention in the next 30 days"
        className="expiring-section-card"
      >
        <div className="expiring-placeholder-box">
          <div className="expiring-placeholder-icon">
            <Clock size={28} />
          </div>
          <div className="expiring-placeholder-text">
            <h4 className="expiring-placeholder-title">No Warranties Expiring Soon</h4>
            <p className="expiring-placeholder-desc">
              All your products are currently in good standing. When receipts and warranty durations are linked, automated countdown alerts will appear here.
            </p>
          </div>
        </div>
      </Card>

      {/* 3. Search & Filter Bar */}
      <div className="dashboard-filter-toolbar">
        <div className="dashboard-search-wrap">
          <Search size={16} className="dashboard-search-icon" />
          <input
            type="text"
            placeholder="Search by product name, brand, model, serial #..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="dashboard-search-input"
          />
        </div>

        <div className="dashboard-dropdown-filters">
          {/* Category Filter Dropdown */}
          <div className="filter-dropdown-item">
            <label className="dropdown-label"><Layers size={13} /> Category:</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="dashboard-select"
            >
              <option value="All">All Categories</option>
              {PRODUCT_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Brand Filter Dropdown */}
          <div className="filter-dropdown-item">
            <label className="dropdown-label"><Tag size={13} /> Brand:</label>
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="dashboard-select"
            >
              {availableBrands.map((brand) => (
                <option key={brand} value={brand}>
                  {brand === 'All' ? 'All Brands' : brand}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 4. Products Section */}
      <div className="dashboard-products-section">
        <div className="section-header-row">
          <div>
            <h3 className="section-title">My Registered Assets</h3>
            <p className="section-subtitle">
              Showing {filteredProducts.length} of {products.length} registered item(s)
            </p>
          </div>
          {products.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              icon={ArrowRight}
              iconPosition="right"
              onClick={() => navigate('/products')}
            >
              Manage Catalog
            </Button>
          )}
        </div>

        {loading ? (
          <LoadingState message="Loading your dashboard..." description="Fetching assets from database..." />
        ) : error ? (
          <div className="dashboard-error-box">
            <AlertCircle size={24} color="var(--danger)" />
            <p>{error}</p>
            <Button variant="outline" size="sm" onClick={fetchProducts}>
              Retry
            </Button>
          </div>
        ) : products.length === 0 ? (
          /* Zero Products State */
          <Card className="dashboard-empty-card">
            <div className="empty-onboarding-box">
              <div className="empty-icon-circle">
                <Package size={36} />
              </div>
              <h4 className="empty-title">Welcome to OWNIT!</h4>
              <p className="empty-desc">
                You haven't registered any physical products yet. Start by adding your electronics, home appliances, or mobile devices to track their full lifecycle.
              </p>
              <Button
                variant="primary"
                icon={Plus}
                size="md"
                onClick={() => setIsAddModalOpen(true)}
              >
                Add Your First Product
              </Button>
            </div>
          </Card>
        ) : filteredProducts.length === 0 ? (
          /* Filter No-Match State */
          <Card className="dashboard-empty-card">
            <div className="empty-onboarding-box">
              <Package size={32} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
              <h4 className="empty-title">No products match your filters</h4>
              <p className="empty-desc">
                Try clearing your search query, category, or brand filter.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchTerm('');
                  setSelectedCategory('All');
                  setSelectedBrand('All');
                }}
              >
                Reset All Filters
              </Button>
            </div>
          </Card>
        ) : (
          /* Product Cards Grid */
          <div className="dashboard-product-grid">
            {filteredProducts.map((product) => {
              const IconComponent = getCategoryIcon(product.category);
              return (
                <Card
                  key={product.id}
                  hoverable
                  className="dashboard-item-card"
                  onClick={() => navigate(`/products/${product.id}`)}
                >
                  <div className="item-card-header">
                    <div className="item-thumbnail">
                      {product.image ? (
                        <img
                          src={product.image}
                          alt={product.name}
                          className="item-img"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div
                        className="item-fallback-icon"
                        style={{ display: product.image ? 'none' : 'flex' }}
                      >
                        <IconComponent size={24} />
                      </div>
                    </div>

                    <div className="item-badges-column">
                      <span className="category-pill">{product.category}</span>
                      {/* Warranty Status Placeholder */}
                      <span className="warranty-status-pill" title="Warranty Status">
                        🟢 Active (Pending Doc)
                      </span>
                    </div>
                  </div>

                  <div className="item-card-body">
                    <span className="item-brand-tag">{product.brand}</span>
                    <h4 className="item-name">{product.name}</h4>
                    <p className="item-model">{product.model}</p>
                  </div>

                  <div className="item-card-details">
                    <div className="item-meta-row">
                      <Calendar size={13} />
                      <span>Purchased: {product.purchaseDate}</span>
                    </div>
                    {product.seller && (
                      <div className="item-meta-row">
                        <Store size={13} />
                        <span>Seller: {product.seller}</span>
                      </div>
                    )}
                  </div>

                  <div className="item-card-footer">
                    <div className="item-price">
                      ₹{product.price.toLocaleString('en-IN')}
                      {product.quantity > 1 && (
                        <span className="item-qty-tag">x{product.quantity}</span>
                      )}
                    </div>
                    <div className="life-score-placeholder" title="Product Life Score">
                      <span className="score-label">Life Score:</span>
                      <span className="score-badge">Pending</span>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Product Modal */}
      <ProductFormModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => {
          fetchProducts();
        }}
      />

      {/* Placeholder Modal: Scan Receipt (OCR) */}
      <Modal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        title="Scan Receipt with Tesseract OCR"
        subtitle="Extract multiple items and warranty dates automatically"
      >
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          <div style={{ width: '64px', height: '64px', margin: '0 auto 16px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={32} />
          </div>
          <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Drag & Drop Receipt / Invoice</h4>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Supports PDF, PNG, JPG (Processed completely locally with Tesseract OCR)
          </p>
          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', gap: '10px' }}>
            <Button variant="outline" onClick={() => setIsScanModalOpen(false)}>Browse Files</Button>
            <Button variant="primary" onClick={() => setIsScanModalOpen(false)}>Simulate OCR Extract</Button>
          </div>
        </div>
      </Modal>
    </PageContainer>
  );
}
