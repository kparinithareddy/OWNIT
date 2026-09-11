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
  Tag,
  RotateCcw,
  Activity,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card, { StatCard } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import ProductFormModal from '../../components/products/ProductFormModal';
import ReceiptScannerModal from '../../components/ocr/ReceiptScannerModal';
import Modal from '../../components/common/Modal';
import { PRODUCT_CATEGORIES } from '../../data/categories';
import { productsApi, warrantiesApi, recallsApi } from '../../services/api';
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
  const [warranties, setWarranties] = useState([]);
  const [lifeScoreMap, setLifeScoreMap] = useState({});
  const [vaultRecalls, setVaultRecalls] = useState([]);
  const [warrantySummary, setWarrantySummary] = useState({
    totalWarranties: 0,
    active: 0,
    expiringSoon: 0,
    expired: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search and filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedBrand, setSelectedBrand] = useState('All');

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [prodData, wList, wSum, recallData] = await Promise.all([
        productsApi.list(),
        warrantiesApi.list(),
        warrantiesApi.getSummary(),
        recallsApi.vaultScan().catch(() => ({ alerts: [] }))
      ]);
      setProducts(prodData || []);
      setWarranties(wList || []);
      setWarrantySummary({
        totalWarranties: wSum?.totalWarranties || 0,
        active: wSum?.activeCount ?? wSum?.active ?? 0,
        expiringSoon: wSum?.expiringSoonCount ?? wSum?.expiringSoon ?? 0,
        expired: wSum?.expiredCount ?? wSum?.expired ?? 0
      });
      setVaultRecalls(recallData?.alerts || []);

      // Async fetch life scores for products in parallel
      if (prodData && prodData.length > 0) {
        Promise.all(
          prodData.map(async (p) => {
            try {
              const res = await productsApi.getLifeScore(p.id);
              return { id: p.id, score: res };
            } catch (err) {
              return { id: p.id, score: null };
            }
          })
        ).then((scoreResults) => {
          const sMap = {};
          scoreResults.forEach((item) => {
            if (item.score) sMap[item.id] = item.score;
          });
          setLifeScoreMap(sMap);
        });
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err.message || 'Failed to connect to backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
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

  // Product ID to warranty components map
  const productWarrantyMap = useMemo(() => {
    const map = {};
    warranties.forEach((w) => {
      if (!map[w.productId]) {
        map[w.productId] = [];
      }
      map[w.productId].push(w);
    });
    return map;
  }, [warranties]);

  // Expiring soon warranty items
  const expiringSoonWarranties = useMemo(() => {
    return warranties.filter((w) => w.status === 'Expiring Soon');
  }, [warranties]);

  // Ending soon return window products
  const endingSoonReturns = useMemo(() => {
    return products.filter((p) => p.returnStatus === 'Ending Soon');
  }, [products]);

  const hasExpiringDeadlines = expiringSoonWarranties.length > 0 || endingSoonReturns.length > 0;

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
      subtitle="Track your physical assets, return deadlines, multi-component warranties, and upcoming expiration milestones."
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
      {/* Safety Recall Alert Banner (if any vault alerts found) */}
      {vaultRecalls.length > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            padding: '1rem 1.25rem',
            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(239, 68, 68, 0.1))',
            border: '1px solid rgba(245, 158, 11, 0.4)',
            borderLeft: '4px solid #f59e0b',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertTriangle size={24} style={{ color: '#f59e0b', flexShrink: 0 }} />
            <div>
              <strong style={{ color: '#fbbf24', fontSize: '0.95rem' }}>
                Safety Advisory: {vaultRecalls.length} product{vaultRecalls.length > 1 ? 's have' : ' has'} a possible recall match.
              </strong>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Possible recall match — verify with the official source. Click on affected assets to view verified bulletins.
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {vaultRecalls.map((alert) => (
              <Button
                key={alert.productId}
                size="xs"
                variant="outline"
                onClick={() => navigate(`/products/${alert.productId}`)}
              >
                {alert.brand} {alert.model || alert.productName}
              </Button>
            ))}
          </div>
        </div>
      )}

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
          value={loading ? '...' : String(warrantySummary.active)}
          subtitle="🟢 Active & protected"
          icon={ShieldCheck}
          variant="success"
        />
        <StatCard
          title="Expiring Soon"
          value={loading ? '...' : String(warrantySummary.expiringSoon + endingSoonReturns.length)}
          subtitle={`🟠 ${warrantySummary.expiringSoon} warranties & ${endingSoonReturns.length} returns`}
          icon={Clock}
          variant="warning"
        />
        <StatCard
          title="Expired"
          value={loading ? '...' : String(warrantySummary.expired)}
          subtitle="🔴 Out of coverage"
          icon={ShieldAlert}
          variant="danger"
        />
      </div>

      {/* 2. Expiring Soon Section */}
      <Card
        title="⏳ Expiring Soon (Warranties & Return Deadlines)"
        subtitle="Monitors critical warranty components and store return windows requiring attention soon"
        className="expiring-section-card"
      >
        {!hasExpiringDeadlines ? (
          <div className="expiring-placeholder-box">
            <div className="expiring-placeholder-icon">
              <Clock size={28} />
            </div>
            <div className="expiring-placeholder-text">
              <h4 className="expiring-placeholder-title">No Deadlines Expiring Soon</h4>
              <p className="expiring-placeholder-desc">
                All your warranties and store return windows are in good standing. When return windows or warranties have 30 or fewer days remaining, active countdown alerts will appear here.
              </p>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {/* Returns Ending Soon */}
            {endingSoonReturns.map((prod) => (
              <div
                key={`ret-${prod.id}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(245, 158, 11, 0.08)',
                  border: '1px solid rgba(245, 158, 11, 0.3)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <RotateCcw size={22} color="#f59e0b" />
                  <div>
                    <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                      Return Window Closing: {prod.name}
                    </h5>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                      Deadline: <strong>{prod.returnDeadline}</strong> ({prod.returnDaysRemaining === 0 ? 'Ends Today' : `${prod.returnDaysRemaining} days left`}) &bull; Seller: {prod.seller || 'Store'}
                    </p>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/products/${prod.id}`)}
                >
                  View Product
                </Button>
              </div>
            ))}

            {/* Warranties Expiring Soon */}
            {expiringSoonWarranties.map((w) => {
              const prod = products.find((p) => p.id === w.productId);
              return (
                <div
                  key={`warr-${w.id}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.3)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <ShieldAlert size={22} color="#f59e0b" />
                    <div>
                      <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                        {prod ? prod.name : 'Linked Product'} — {w.type}
                      </h5>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                        Provider: <strong>{w.provider}</strong> &bull; Expires on: <strong>{w.expiryDate}</strong> ({w.daysRemaining} days remaining)
                      </p>
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/products/${w.productId}`)}
                  >
                    View Warranty
                  </Button>
                </div>
              );
            })}
          </div>
        )}
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
            <Button variant="outline" size="sm" onClick={fetchDashboardData}>
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
              const pWarranties = productWarrantyMap[product.id] || [];
              const hasExpiring = pWarranties.some((w) => w.status === 'Expiring Soon');
              const hasActive = pWarranties.some((w) => w.status === 'Active');
              const allExpired = pWarranties.length > 0 && pWarranties.every((w) => w.status === 'Expired');

              let warrantyBadgeLabel = 'No Warranty';
              if (hasExpiring) {
                warrantyBadgeLabel = '🟠 Warranty Expiring Soon';
              } else if (hasActive) {
                warrantyBadgeLabel = '🟢 Warranty Active';
              } else if (allExpired) {
                warrantyBadgeLabel = '🔴 Warranty Expired';
              }

              // Return badge
              const retStatus = product.returnStatus;
              let returnBadgeLabel = null;
              if (retStatus === 'Active') {
                returnBadgeLabel = `🟢 Return: ${product.returnDaysRemaining}d left`;
              } else if (retStatus === 'Ending Soon') {
                returnBadgeLabel = `🟠 Return Ends: ${product.returnDaysRemaining}d`;
              } else if (retStatus === 'Expired') {
                returnBadgeLabel = '🔴 Return Closed';
              }

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
                      {returnBadgeLabel && (
                        <span className="warranty-status-pill" title="Store Return Status" style={{ fontSize: '0.6875rem' }}>
                          {returnBadgeLabel}
                        </span>
                      )}
                      <span className="warranty-status-pill" title="Warranty Status">
                        {warrantyBadgeLabel}
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
                    {lifeScoreMap[product.id] ? (
                      <div
                        className={`dashboard-life-score-pill ${lifeScoreMap[product.id].color}`}
                        title={`Life Score: ${lifeScoreMap[product.id].score}/100 (${lifeScoreMap[product.id].grade})`}
                      >
                        <Activity size={12} />
                        <span className="dash-score-num">{lifeScoreMap[product.id].score}</span>
                        <span className="dash-score-grade">{lifeScoreMap[product.id].grade}</span>
                      </div>
                    ) : (
                      <div className="life-score-placeholder" title="Warranty Components">
                        <span className="score-label">Coverage:</span>
                        <span className="score-badge">{pWarranties.length} Tier(s)</span>
                      </div>
                    )}
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
          fetchDashboardData();
        }}
      />

      {/* Interactive Receipt OCR Confirmation Modal */}
      <ReceiptScannerModal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        onProductsSaved={() => {
          fetchDashboardData();
        }}
      />
    </PageContainer>
  );
}
