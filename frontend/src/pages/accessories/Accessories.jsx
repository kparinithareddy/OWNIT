import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  PlugZap,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Filter,
  DollarSign,
  Package,
  Layers,
  Star,
  RefreshCw,
  SlidersHorizontal,
  Store,
  Info
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Input, { Select } from '../../components/common/Input';
import LoadingState from '../../components/common/LoadingState';
import { productsApi, accessoriesApi } from '../../services/api';
import { useLanguage, useLocalizedList } from '../../i18n/LanguageContext';
import './Accessories.css';

const BUDGET_PRESETS = [
  { id: 'all', label: 'All Budgets', min: null, max: null },
  { id: 'under-1k', label: 'Under ₹1,500', min: 0, max: 1500 },
  { id: '1k-5k', label: '₹1,500 – ₹5,000', min: 1500, max: 5000 },
  { id: '5k-10k', label: '₹5,000 – ₹10,000', min: 5000, max: 10000 },
  { id: 'above-10k', label: 'Above ₹10,000', min: 10000, max: null }
];

export default function Accessories() {
  const { t } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlProductId = searchParams.get('productId');

  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(urlProductId || '');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [availableCategories, setAvailableCategories] = useState([]);
  
  // Budget filter state
  const [selectedBudgetPreset, setSelectedBudgetPreset] = useState('all');
  const [customMinBudget, setCustomMinBudget] = useState('');
  const [customMaxBudget, setCustomMaxBudget] = useState('');

  const [recommendations, setRecommendations] = useState([]);
  const localizedRecommendations = useLocalizedList(recommendations, ['name', 'category', 'compatibilityReason', 'platform']);
  const [productMetadata, setProductMetadata] = useState(null);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [error, setError] = useState(null);

  // 1. Fetch user products on mount
  useEffect(() => {
    async function loadProducts() {
      try {
        setLoadingProducts(true);
        const prodList = await productsApi.list();
        setProducts(prodList || []);
        
        // Auto-select first product if none selected
        if (!selectedProductId && prodList && prodList.length > 0) {
          setSelectedProductId(prodList[0].id);
        }
      } catch (err) {
        console.error('Failed to load products:', err);
        setError('Could not load your registered products.');
      } finally {
        setLoadingProducts(false);
      }
    }
    loadProducts();
  }, []);

  // 2. Fetch categories and recommendations when product or filters change
  const fetchRecommendations = useCallback(async () => {
    if (!selectedProductId) return;

    try {
      setLoadingRecs(true);
      setError(null);

      // Determine active budget bounds
      let minBudget = null;
      let maxBudget = null;

      if (selectedBudgetPreset !== 'custom') {
        const preset = BUDGET_PRESETS.find((p) => p.id === selectedBudgetPreset);
        if (preset) {
          minBudget = preset.min;
          maxBudget = preset.max;
        }
      } else {
        if (customMinBudget !== '') minBudget = parseFloat(customMinBudget);
        if (customMaxBudget !== '') maxBudget = parseFloat(customMaxBudget);
      }

      // Parallel fetch categories and recommendations
      const [recsData, catsData] = await Promise.all([
        accessoriesApi.getRecommendations({
          productId: selectedProductId,
          category: selectedCategory,
          minBudget: minBudget,
          maxBudget: maxBudget
        }),
        accessoriesApi.getCategories(selectedProductId)
      ]);

      setRecommendations(recsData.recommendations || []);
      setProductMetadata({
        productName: recsData.productName,
        brand: recsData.brand,
        model: recsData.model,
        category: recsData.category
      });
      setAvailableCategories(catsData || []);
    } catch (err) {
      console.error('Failed to load accessory recommendations:', err);
      setError(err.message || 'Could not retrieve accessory recommendations.');
    } finally {
      setLoadingRecs(false);
    }
  }, [selectedProductId, selectedCategory, selectedBudgetPreset, customMinBudget, customMaxBudget]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const handleProductChange = (e) => {
    const newId = e.target.value;
    setSelectedProductId(newId);
    setSelectedCategory('All');
    setSearchParams(newId ? { productId: newId } : {});
  };

  const handleBudgetPresetClick = (presetId) => {
    setSelectedBudgetPreset(presetId);
  };

  const handleClearFilters = () => {
    setSelectedCategory('All');
    setSelectedBudgetPreset('all');
    setCustomMinBudget('');
    setCustomMaxBudget('');
  };

  const selectedProduct = products.find((p) => p.id === selectedProductId);

  return (
    <PageContainer
      title={t('accessories.title', {}, 'Compatible Accessories & Upgrades')}
      subtitle={t('accessories.subtitle', {}, 'Smart recommendations for mounts, cables, soundbars, and power accessories grounded in your device model.')}
    >
      {/* Top Filter & Product Bar */}
      <Card className="accessories-controls-card" padding="md">
        <div className="accessories-controls-grid">
          {/* Target Product Selector */}
          <div className="control-col product-select-col">
            <label className="control-label">
              <Package size={15} /> {t('accessories.selectProduct', {}, 'Target Product')}
            </label>
            <select
              className="accessories-product-dropdown"
              value={selectedProductId}
              onChange={handleProductChange}
              disabled={loadingProducts || products.length === 0}
            >
              {products.length === 0 ? (
                <option value="">No registered products found</option>
              ) : (
                products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.brand} {p.name} {p.model ? `(${p.model})` : ''} • {p.category}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Active Product Specs Badge Bar */}
          {productMetadata && (
            <div className="control-col product-meta-col">
              <div className="product-spec-pill">
                <span className="spec-label">Brand:</span>
                <span className="spec-val">{productMetadata.brand}</span>
              </div>
              <div className="product-spec-pill">
                <span className="spec-label">Model:</span>
                <code className="spec-code">{productMetadata.model || 'Standard'}</code>
              </div>
              <div className="product-spec-pill">
                <span className="spec-label">Category:</span>
                <span className="spec-val">{productMetadata.category}</span>
              </div>
            </div>
          )}
        </div>

        {/* Budget Filter Strip */}
        <div className="accessories-filter-section">
          <div className="filter-row">
            <span className="filter-label">
              <DollarSign size={14} /> {t('accessories.budgetFilter', {}, 'Budget Filter')}:
            </span>
            <div className="preset-pill-group">
              {BUDGET_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  className={`preset-pill-btn ${selectedBudgetPreset === preset.id ? 'active' : ''}`}
                  onClick={() => handleBudgetPresetClick(preset.id)}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter Strip */}
          {availableCategories.length > 0 && (
            <div className="filter-row" style={{ marginTop: '12px' }}>
              <span className="filter-label">
                <Layers size={14} /> {t('accessories.categoryFilter', {}, 'Category Filter')}:
              </span>
              <div className="preset-pill-group">
                <button
                  className={`preset-pill-btn ${selectedCategory === 'All' ? 'active' : ''}`}
                  onClick={() => setSelectedCategory('All')}
                >
                  {t('accessories.allCategories', {}, 'All Categories')}
                </button>
                {availableCategories.map((cat) => (
                  <button
                    key={cat}
                    className={`preset-pill-btn ${selectedCategory.toLowerCase() === cat.toLowerCase() ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Main Recommendations Display */}
      {loadingRecs ? (
        <div className="accessories-loading-state">
          <RefreshCw size={24} className="spinning" />
          <p>Analyzing product specifications and compatibility catalog...</p>
        </div>
      ) : error ? (
        <Card className="accessories-error-card">
          <AlertCircle size={24} color="var(--status-danger)" />
          <p>{error}</p>
          <Button variant="outline" size="sm" onClick={fetchRecommendations}>
            Retry
          </Button>
        </Card>
      ) : localizedRecommendations.length === 0 ? (
        <Card className="accessories-empty-card" padding="lg">
          <PlugZap size={40} className="empty-icon" />
          <h4>{t('accessories.noAccessories', {}, 'No accessories matching your budget and category filters.')}</h4>
          <p>Try clearing budget restrictions or selecting a different accessory category.</p>
          <Button variant="outline" size="sm" onClick={handleClearFilters}>
            {t('accessories.clearFilters', {}, 'Clear Filters')}
          </Button>
        </Card>
      ) : (
        <div className="accessories-grid">
          {localizedRecommendations.map((acc) => {
            const isCompatible = acc.compatibilityStatus === 'Compatible';
            const safeSourceUrl = acc.sourceUrl || `https://www.amazon.in/s?k=${encodeURIComponent(`${acc.brand || ''} ${acc.name || ''}`.trim())}`;
            return (
              <Card key={acc.id} className="accessory-card" padding="md">
                {/* Header: Category + Compatibility Badge */}
                <div className="accessory-top">
                  <span className="accessory-category-badge">
                    {acc.category.toUpperCase()}
                  </span>
                  <div
                    className={`compat-status-tag ${isCompatible ? 'compat-verified' : 'compat-potential'}`}
                    title={isCompatible ? 'Verified model/spec match' : 'Universal standard compatibility'}
                  >
                    {isCompatible ? (
                      <>
                        <CheckCircle2 size={13} />
                        <span>{t('accessories.compatible', {}, 'Compatible')}</span>
                      </>
                    ) : (
                      <>
                        <Info size={13} />
                        <span>{t('accessories.potentiallyCompatible', {}, 'Potentially compatible')}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Body Details */}
                <div className="accessory-body">
                  <h4 className="accessory-title" title={acc.name}>
                    {acc.name}
                  </h4>

                  {/* Brand & Model tag */}
                  <div className="accessory-brand-row">
                    <span className="acc-brand">{acc.brand}</span>
                    {acc.model && <code className="acc-model">{acc.model}</code>}
                  </div>

                  {/* Compatibility Evidence Box */}
                  <div className={`accessory-evidence-box ${isCompatible ? 'evidence-verified' : 'evidence-potential'}`}>
                    <div className="evidence-header">
                      <span className="evidence-title">
                        {t('accessories.evidence', {}, 'Compatibility Evidence')}:
                      </span>
                    </div>
                    <p className="evidence-text">{acc.compatibilityReason}</p>
                  </div>

                  {/* Ratings & Reviews */}
                  {acc.rating && (
                    <div className="accessory-rating-row">
                      <div className="rating-badge">
                        <Star size={12} className="star-icon" fill="#f59e0b" color="#f59e0b" />
                        <span>{acc.rating.toFixed(1)}</span>
                      </div>
                      {acc.reviewCount && (
                        <span className="review-count">
                          ({acc.reviewCount.toLocaleString()} {t('accessories.reviews', {}, 'reviews')})
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer: Price + Direct Source Link */}
                <div className="accessory-footer">
                  <div className="acc-price-box">
                    <span className="acc-price-val">{acc.priceFormatted}</span>
                    <span className="acc-platform">
                      <Store size={12} /> {acc.platform}
                    </span>
                  </div>

                  <a
                    href={safeSourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="acc-source-btn"
                    title={`Open verified listing on ${acc.platform || 'Store'}`}
                  >
                    <span>{t('accessories.openSource', {}, 'Open Source')}</span>
                    <ExternalLink size={13} />
                  </a>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
