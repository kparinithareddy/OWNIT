import React, { useState, useEffect, useCallback } from 'react';
import {
  Bot,
  Sparkles,
  Cpu,
  Package,
  Layers,
  HelpCircle,
  AlertCircle
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import ProductAIChatWidget from '../../components/ai/ProductAIChatWidget';
import { productsApi, warrantiesApi, documentsApi, maintenanceApi, aiApi } from '../../services/api';
import './AIAssistant.css';

export default function AIAssistant() {
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [productData, setProductData] = useState({
    product: null,
    warranties: [],
    documents: [],
    maintenanceRecords: []
  });
  const [loading, setLoading] = useState(true);
  const [loadingProductDetails, setLoadingProductDetails] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);

  // 1. Fetch user's registered products & Ollama status
  const fetchInitialData = useCallback(async () => {
    try {
      setLoading(true);
      const [prodList, statusRes] = await Promise.all([
        productsApi.list(),
        aiApi.getStatus().catch(() => ({ isAvailable: false, configuredModel: 'llama3.2', provider: 'Ollama' }))
      ]);
      setProducts(prodList);
      setAiStatus(statusRes);
      if (prodList && prodList.length > 0) {
        setSelectedProductId(prodList[0].id);
      }
    } catch (err) {
      console.error('Error fetching initial products for AI Assistant:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // 2. When selected product changes, fetch its warranties, documents, maintenance
  const fetchSelectedProductDetails = useCallback(async (prodId) => {
    if (!prodId) return;
    try {
      setLoadingProductDetails(true);
      const [prod, wList, dList, mList] = await Promise.all([
        productsApi.get(prodId),
        warrantiesApi.getByProduct(prodId),
        documentsApi.list({ productId: prodId }),
        maintenanceApi.listByProduct(prodId)
      ]);
      setProductData({
        product: prod,
        warranties: wList,
        documents: dList,
        maintenanceRecords: mList
      });
    } catch (err) {
      console.error('Error fetching details for selected product:', err);
    } finally {
      setLoadingProductDetails(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProductId) {
      fetchSelectedProductDetails(selectedProductId);
    }
  }, [selectedProductId, fetchSelectedProductDetails]);

  return (
    <PageContainer
      title="Product AI Assistant"
      subtitle="Context-aware, private assistant anchored to your specific product documents, warranties, and maintenance records."
      actions={
        <div className="ai-status-tag">
          <Cpu size={16} />
          <span>
            {aiStatus?.isAvailable
              ? `Local Engine: ${aiStatus.configuredModel} (Ollama)`
              : 'Local Engine: Offline Fallback'}
          </span>
        </div>
      }
    >
      {loading ? (
        <LoadingState message="Loading AI Assistant..." description="Checking local Ollama status and catalog..." />
      ) : products.length === 0 ? (
        <Card className="dashboard-empty-card">
          <div className="empty-onboarding-box">
            <Package size={36} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
            <h4 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-main)' }}>
              No Products Registered
            </h4>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: '8px 0 16px' }}>
              Add a physical item (e.g. laptop, TV, mobile) in the catalog to begin context-anchored AI conversations.
            </p>
          </div>
        </Card>
      ) : (
        <div className="ai-chat-layout">
          {/* Left Side: Product Selector */}
          <div className="ai-sidebar-col">
            <Card title="Active Target Asset" subtitle="All AI reasoning is anchored to this product">
              <div className="product-selector-group">
                <label className="selector-label">Select Registered Product:</label>
                <select
                  className="ai-product-select"
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.brand})
                    </option>
                  ))}
                </select>
              </div>

              {productData.product && (
                <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                  <div><strong>Category:</strong> {productData.product.category}</div>
                  <div><strong>Model:</strong> {productData.product.model}</div>
                  <div><strong>Warranties:</strong> {productData.warranties.length} Component(s)</div>
                  <div><strong>Documents:</strong> {productData.documents.length} Attached</div>
                  <div><strong>Maintenance:</strong> {productData.maintenanceRecords.length} Log(s)</div>
                </div>
              )}
            </Card>
          </div>

          {/* Right Side: Chat Window */}
          <div className="ai-chat-col">
            {loadingProductDetails || !productData.product ? (
              <LoadingState message="Connecting to product records..." />
            ) : (
              <ProductAIChatWidget
                product={productData.product}
                warranties={productData.warranties}
                documents={productData.documents}
                maintenanceRecords={productData.maintenanceRecords}
              />
            )}
          </div>
        </div>
      )}
    </PageContainer>
  );
}

