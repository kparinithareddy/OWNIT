import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  Layers,
  Filter,
  X,
  RotateCcw,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Wrench,
  ArrowUpDown,
  Tag
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import ProductFormModal from '../../components/products/ProductFormModal';
import ReceiptScannerModal from '../../components/ocr/ReceiptScannerModal';
import { PRODUCT_CATEGORIES } from '../../data/categories';
import { productsApi } from '../../services/api';
import { useLanguage, useLocalizedList } from '../../i18n/LanguageContext';
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
  const { t } = useLanguage();

  const [products, setProducts] = useState([]);
  const localizedProducts = useLocalizedList(products, ['name', 'category', 'seller']);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search & Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedBrand, setSelectedBrand] = useState('All');
  const [warrantyStatus, setWarrantyStatus] = useState('all');
  const [returnStatus, setReturnStatus] = useState('all');
  const [maintenanceStatus, setMaintenanceStatus] = useState('all');
  const [sortOption, setSortOption] = useState('createdAt:desc');

  // Modals state
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [deletingProductId, setDeletingProductId] = useState(null);

  // Check if any filter is active
  const hasActiveFilters = useMemo(() => {
    return (
      (searchTerm && searchTerm.trim().length > 0) ||
      selectedCategory !== 'All' ||
      selectedBrand !== 'All' ||
      warrantyStatus !== 'all' ||
      returnStatus !== 'all' ||
      maintenanceStatus !== 'all'
    );
  }, [searchTerm, selectedCategory, selectedBrand, warrantyStatus, returnStatus, maintenanceStatus]);

  // Fetch unique brands
  const fetchBrands = useCallback(async () => {
    try {
      const brandList = await productsApi.getBrands();
      setBrands(brandList || []);
    } catch (err) {
      console.warn('Could not fetch brand list:', err);
    }
  }, []);

  useEffect(() => {
    fetchBrands();
  }, [fetchBrands]);

  // Fetch products with full server-side filtering
  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [sortBy, sortOrder] = sortOption.split(':');

      const data = await productsApi.list({
        search: searchTerm,
        category: selectedCategory,
        brand: selectedBrand,
        warrantyStatus: warrantyStatus,
        returnStatus: returnStatus,
        maintenanceStatus: maintenanceStatus,
        sortBy: sortBy || 'createdAt',
        sortOrder: sortOrder || 'desc'
      });

      setProducts(data || []);
    } catch (err) {
      console.error('Error fetching products:', err);
      setError(err.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  }, [searchTerm, selectedCategory, selectedBrand, warrantyStatus, returnStatus, maintenanceStatus, sortOption]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProducts();
    }, 200);
    return () => clearTimeout(timer);
  }, [fetchProducts]);

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedCategory('All');
    setSelectedBrand('All');
    setWarrantyStatus('all');
    setReturnStatus('all');
    setMaintenanceStatus('all');
    setSortOption('createdAt:desc');
  };

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
      fetchBrands();
    } catch (err) {
      alert(`Could not delete product: ${err.message}`);
    } finally {
      setDeletingProductId(null);
    }
  };

  const categories = ['All', ...PRODUCT_CATEGORIES];

  const getLocalizedCategoryName = (cat) => {
    if (!cat) return '';
    if (cat === 'All') return t('products.allCategories', {}, 'All Categories');
    return t(`categories.${cat}`, {}, cat);
  };

  return (
    <PageContainer
      title={t('products.title', {}, 'Product Inventory')}
      subtitle={t('products.subtitle', {}, 'Manage and monitor all your physical electronics, appliances, and assets.')}
      actions={
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Button
            variant="outline"
            icon={<Sparkles size={16} />}
            onClick={() => setIsScannerOpen(true)}
          >
            {t('products.scanReceipt', {}, 'Scan Receipt')}
          </Button>
          <Button
            variant="primary"
            icon={<Plus size={16} />}
            onClick={handleOpenAdd}
          >
            {t('products.addNewProduct', {}, 'Add Product')}
          </Button>
        </div>
      }
    >
      {/* Search & Comprehensive Filters Toolbar */}
      <div className="product-filter-bar">
        {/* Top row: Search input & Sort dropdown */}
        <div className="product-search-sort-row">
          <div className="product-search-box">
            <Search size={16} className="product-search-icon" />
            <input
              type="text"
              placeholder={t('products.searchPlaceholder', {}, 'Search by product name, brand, model, or serial number...')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="product-search-input"
            />
            {searchTerm && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => setSearchTerm('')}
                title="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="product-sort-box">
            <ArrowUpDown size={15} className="sort-icon" />
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value)}
              className="product-filter-select"
            >
              <option value="createdAt:desc">{t('products.newestFirst', {}, 'Newest Added')}</option>
              <option value="createdAt:asc">{t('products.oldestFirst', {}, 'Oldest Added')}</option>
              <option value="price:desc">{t('products.priceHighLow', {}, 'Price: High to Low')}</option>
              <option value="price:asc">{t('products.priceLowHigh', {}, 'Price: Low to High')}</option>
              <option value="name:asc">{t('products.nameAsc', {}, 'Name: A to Z')}</option>
              <option value="purchaseDate:desc">{t('products.purchaseDateDesc', {}, 'Purchase Date: Newest')}</option>
            </select>
          </div>
        </div>

        {/* Category Pill Filters */}
        <div className="filter-group-category">
          <span className="filter-label"><Layers size={14} /> {t('products.filterCategory', {}, 'Category')}:</span>
          <div className="filter-pills">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`filter-pill ${selectedCategory === cat ? 'filter-pill-active' : ''}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {getLocalizedCategoryName(cat)}
              </button>
            ))}
          </div>
        </div>

        {/* Dropdown Filters Row: Brand, Warranty, Return, Maintenance */}
        <div className="product-filter-dropdowns-row">
          {/* Brand Filter */}
          <div className="filter-select-wrapper">
            <span className="filter-mini-label"><Tag size={12} /> {t('products.filterBrand', {}, 'Brand')}</span>
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="product-filter-select"
            >
              <option value="All">{t('products.allBrands', {}, 'All Brands')}</option>
              {brands.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>

          {/* Warranty Filter */}
          <div className="filter-select-wrapper">
            <span className="filter-mini-label"><ShieldCheck size={12} /> {t('products.filterWarranty', {}, 'Warranty')}</span>
            <select
              value={warrantyStatus}
              onChange={(e) => setWarrantyStatus(e.target.value)}
              className="product-filter-select"
            >
              <option value="all">{t('products.allWarranties', {}, 'All Warranties')}</option>
              <option value="active">🟢 {t('products.activeWarranty', {}, 'Active Coverage')}</option>
              <option value="expiring_soon">🟠 {t('products.expiringSoonWarranty', {}, 'Expiring Soon (≤30d)')}</option>
              <option value="expired">🔴 {t('products.expiredWarranty', {}, 'Expired Warranty')}</option>
            </select>
          </div>

          {/* Return Window Filter */}
          <div className="filter-select-wrapper">
            <span className="filter-mini-label"><Clock size={12} /> {t('products.filterReturn', {}, 'Return Window')}</span>
            <select
              value={returnStatus}
              onChange={(e) => setReturnStatus(e.target.value)}
              className="product-filter-select"
            >
              <option value="all">{t('products.allReturns', {}, 'All Returns')}</option>
              <option value="active">🟢 {t('products.activeReturn', {}, 'Active Return Window')}</option>
              <option value="expired">🔴 {t('products.expiredReturn', {}, 'Return Window Closed')}</option>
            </select>
          </div>

          {/* Maintenance Status Filter */}
          <div className="filter-select-wrapper">
            <span className="filter-mini-label"><Wrench size={12} /> {t('products.filterMaintenance', {}, 'Maintenance')}</span>
            <select
              value={maintenanceStatus}
              onChange={(e) => setMaintenanceStatus(e.target.value)}
              className="product-filter-select"
            >
              <option value="all">{t('products.allMaintenance', {}, 'All Maintenance')}</option>
              <option value="due">🟠 {t('products.maintenanceDue', {}, 'Due Soon / Needs Attention')}</option>
              <option value="overdue">🔴 {t('products.maintenanceOverdue', {}, 'Overdue Maintenance')}</option>
              <option value="up_to_date">🟢 {t('products.maintenanceUpToDate', {}, 'Up to Date')}</option>
            </select>
          </div>
        </div>

        {/* Active Filters Summary Bar */}
        {hasActiveFilters && (
          <div className="active-filters-bar">
            <div className="active-filters-chips">
              <span className="active-filters-title">{t('products.activeFilters', {}, 'Active Filters')}:</span>

              {searchTerm && (
                <span className="filter-chip">
                  Search: "{searchTerm}"
                  <button type="button" onClick={() => setSearchTerm('')}><X size={12} /></button>
                </span>
              )}

              {selectedCategory !== 'All' && (
                <span className="filter-chip">
                  {getLocalizedCategoryName(selectedCategory)}
                  <button type="button" onClick={() => setSelectedCategory('All')}><X size={12} /></button>
                </span>
              )}

              {selectedBrand !== 'All' && (
                <span className="filter-chip">
                  {t('products.brand', {}, 'Brand')}: {selectedBrand}
                  <button type="button" onClick={() => setSelectedBrand('All')}><X size={12} /></button>
                </span>
              )}

              {warrantyStatus !== 'all' && (
                <span className="filter-chip">
                  {t('products.filterWarranty', {}, 'Warranty')}: {warrantyStatus === 'active' ? t('common.active', {}, 'Active') : warrantyStatus === 'expiring_soon' ? t('common.expiringSoon', {}, 'Expiring Soon') : t('common.expired', {}, 'Expired')}
                  <button type="button" onClick={() => setWarrantyStatus('all')}><X size={12} /></button>
                </span>
              )}

              {returnStatus !== 'all' && (
                <span className="filter-chip">
                  {t('products.filterReturn', {}, 'Return')}: {returnStatus === 'active' ? t('common.active', {}, 'Active') : t('common.expired', {}, 'Closed')}
                  <button type="button" onClick={() => setReturnStatus('all')}><X size={12} /></button>
                </span>
              )}

              {maintenanceStatus !== 'all' && (
                <span className="filter-chip">
                  {t('products.filterMaintenance', {}, 'Maintenance')}: {maintenanceStatus === 'due' ? t('products.maintenanceDue', {}, 'Due Soon') : maintenanceStatus === 'overdue' ? t('products.maintenanceOverdue', {}, 'Overdue') : t('products.maintenanceUpToDate', {}, 'Up to date')}
                  <button type="button" onClick={() => setMaintenanceStatus('all')}><X size={12} /></button>
                </span>
              )}
            </div>

            <button
              type="button"
              className="reset-filters-btn"
              onClick={handleResetFilters}
            >
              <RotateCcw size={13} />
              {t('products.resetFilters', {}, 'Reset Filters')}
            </button>
          </div>
        )}
      </div>

      {/* Results Count Header */}
      {!loading && (
        <div className="product-results-header">
          <span className="product-count-text">
            {t('products.showingProducts', { count: products.length, plural: products.length === 1 ? '' : 's' }, `Showing ${products.length} product${products.length === 1 ? '' : 's'}`)}
          </span>
        </div>
      )}

      {/* Main Content Area: Loading / Error / Empty / Grid */}
      {loading && products.length === 0 ? (
        <LoadingState message={t('common.loading', {}, 'Loading products...')} description="Filtering MongoDB indexed vault records..." />
      ) : error ? (
        <ErrorState
          title={t('common.error', {}, 'Could not load products')}
          description={error}
          onRetry={fetchProducts}
        />
      ) : localizedProducts.length === 0 ? (
        <EmptyState
          title={
            hasActiveFilters
              ? t('products.noFilteredProducts', {}, 'No products match your search or filters')
              : t('products.emptyTitle', {}, 'No products added yet')
          }
          description={
            hasActiveFilters
              ? t('products.noFilteredProductsDesc', {}, 'Try adjusting your search keywords, category selection, or clearing active filters.')
              : t('products.emptyDesc', {}, 'Get started by adding your first laptop, smartphone, or household appliance!')
          }
          actionLabel={
            hasActiveFilters
              ? t('products.resetFilters', {}, 'Clear Filters')
              : t('products.addNewProduct', {}, 'Add First Product')
          }
          onAction={() => {
            if (hasActiveFilters) {
              handleResetFilters();
            } else {
              handleOpenAdd();
            }
          }}
        />
      ) : (
        <div className="product-grid">
          {localizedProducts.map((product) => {
            const IconComponent = getCategoryIcon(product.category);
            const categoryName = getLocalizedCategoryName(product.category);
            return (
              <Card
                key={product.id}
                hoverable
                className="product-card"
                onClick={() => navigate(`/products/${product.id}`)}
              >
                <div className="product-card-top">
                  <div className="product-avatar">
                    <IconComponent size={20} />
                  </div>
                  <div className="product-card-top-badges">
                    <span className="product-brand-tag">{product.brand}</span>
                    <Badge variant="info" size="sm">
                      {categoryName}
                    </Badge>
                  </div>
                </div>

                <div className="product-card-info">
                  <h3 className="product-title" title={product.name}>{product.name}</h3>
                  {product.model && (
                    <div className="product-model-row">
                      <span className="product-model-chip">
                        <Hash size={11} /> {t('products.model', {}, 'Model')}: {product.model}
                      </span>
                    </div>
                  )}
                </div>

                <div className="product-card-meta">
                  <div className="product-meta-item">
                    <Calendar size={13} />
                    <span>{t('products.purchaseDate', {}, 'Purchased')}: {product.purchaseDate}</span>
                  </div>
                  {product.seller && (
                    <div className="product-meta-item">
                      <Store size={13} />
                      <span>{t('products.seller', {}, 'Store')}: {product.seller}</span>
                    </div>
                  )}
                  {product.serialNumber && (
                    <div className="product-meta-item">
                      <Hash size={13} />
                      <span>{t('products.serialNumber', {}, 'Serial')}: {product.serialNumber}</span>
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
                      title={t('common.edit', {}, 'Edit')}
                      onClick={(e) => handleOpenEdit(e, product)}
                    >
                      <Edit2 size={15} />
                    </button>
                    <button
                      className="card-icon-action-btn action-danger"
                      title={t('common.delete', {}, 'Delete')}
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
          fetchBrands();
        }}
      />

      {/* Receipt OCR Confirmation Modal */}
      <ReceiptScannerModal
        isOpen={isScannerOpen}
        onClose={() => setIsScannerOpen(false)}
        onProductsSaved={() => {
          fetchProducts();
          fetchBrands();
        }}
      />
    </PageContainer>
  );
}
