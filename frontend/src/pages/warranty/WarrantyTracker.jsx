import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Clock,
  Plus,
  ArrowRight,
  ExternalLink,
  Package,
  Layers,
  Calendar,
  AlertCircle
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card, { StatCard } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import { warrantiesApi, productsApi } from '../../services/api';
import './WarrantyTracker.css';

export default function WarrantyTracker() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('All'); // 'All' | 'Active' | 'Expiring Soon' | 'Expired'
  const [warranties, setWarranties] = useState([]);
  const [productsMap, setProductsMap] = useState({});
  const [summary, setSummary] = useState({
    totalWarranties: 0,
    active: 0,
    expiringSoon: 0,
    expired: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchWarrantiesData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [wList, wSummary, prodList] = await Promise.all([
        warrantiesApi.list(),
        warrantiesApi.getSummary(),
        productsApi.list()
      ]);
      setWarranties(wList || []);
      setSummary({
        totalWarranties: wSummary?.totalWarranties || (wList || []).length || 0,
        active: wSummary?.activeCount ?? wSummary?.active ?? 0,
        expiringSoon: wSummary?.expiringSoonCount ?? wSummary?.expiringSoon ?? 0,
        expired: wSummary?.expiredCount ?? wSummary?.expired ?? 0
      });

      const pMap = {};
      prodList.forEach((p) => {
        pMap[p.id] = p;
      });
      setProductsMap(pMap);
    } catch (err) {
      console.error('Error loading warranties:', err);
      setError(err.message || 'Failed to fetch warranty records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarrantiesData();
  }, []);

  const filteredItems = warranties.filter((item) => {
    if (filter === 'All') return true;
    return item.status === filter;
  });

  return (
    <PageContainer
      title="Warranty & Coverage Tracker"
      subtitle="Monitor multi-component coverage validity, expiration countdowns, and service details across all purchases."
      actions={
        <Button
          variant="primary"
          icon={Package}
          onClick={() => navigate('/products')}
        >
          View Registered Assets
        </Button>
      }
    >
      {/* Metric Cards */}
      <div className="warranty-stats-grid">
        <StatCard
          title="Active Coverage"
          value={loading ? '...' : `${summary.active} Components`}
          subtitle="🟢 Active & valid protection"
          icon={ShieldCheck}
          variant="success"
        />
        <StatCard
          title="Expiring Within 30 Days"
          value={loading ? '...' : `${summary.expiringSoon} Components`}
          subtitle="🟠 Action required soon"
          icon={ShieldAlert}
          variant="warning"
        />
        <StatCard
          title="Expired Coverage"
          value={loading ? '...' : `${summary.expired} Components`}
          subtitle="🔴 Out of warranty period"
          icon={Clock}
          variant="danger"
        />
      </div>

      {/* Filter Tabs */}
      <div className="warranty-filters">
        <button
          className={`warranty-filter-btn ${filter === 'All' ? 'active' : ''}`}
          onClick={() => setFilter('All')}
        >
          All Components ({warranties.length})
        </button>
        <button
          className={`warranty-filter-btn ${filter === 'Active' ? 'active' : ''}`}
          onClick={() => setFilter('Active')}
        >
          🟢 Active ({summary.active})
        </button>
        <button
          className={`warranty-filter-btn ${filter === 'Expiring Soon' ? 'active' : ''}`}
          onClick={() => setFilter('Expiring Soon')}
        >
          🟠 Expiring Soon ({summary.expiringSoon})
        </button>
        <button
          className={`warranty-filter-btn ${filter === 'Expired' ? 'active' : ''}`}
          onClick={() => setFilter('Expired')}
        >
          🔴 Expired ({summary.expired})
        </button>
      </div>

      {loading ? (
        <LoadingState message="Loading warranty tracker..." description="Calculating coverage periods..." />
      ) : error ? (
        <div className="dashboard-error-box" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '16px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '8px' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      ) : filteredItems.length === 0 ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '36px 16px' }}>
            <ShieldCheck size={40} style={{ color: 'var(--text-light)', marginBottom: '10px' }} />
            <h4 style={{ fontSize: '1.0625rem', fontWeight: 600, color: 'var(--text-main)' }}>
              {filter === 'All' ? 'No warranty components registered yet' : `No ${filter.toLowerCase()} warranties`}
            </h4>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '440px', margin: '6px auto 16px' }}>
              Open any registered product and click "+ Add Warranty" to record comprehensive, panel, compressor, or extended warranties.
            </p>
            <Button variant="primary" onClick={() => navigate('/products')}>
              Browse Registered Products
            </Button>
          </div>
        </Card>
      ) : (
        /* Warranty List */
        <div className="warranty-cards-list">
          {filteredItems.map((item) => {
            const product = productsMap[item.productId];
            const isExpiring = item.status === 'Expiring Soon';
            const isExpired = item.status === 'Expired';
            const badgeVariant = isExpiring ? 'warning' : isExpired ? 'danger' : 'active';

            return (
              <Card key={item.id} className="warranty-card" padding="md">
                <div className="warranty-card-main">
                  <div className="warranty-card-left">
                    <div className="warranty-avatar">
                      <ShieldCheck size={24} />
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <h3 className="warranty-prod-title">
                          {product ? product.name : 'Linked Product'}
                        </h3>
                        <Badge variant="neutral" size="sm">
                          {item.type}
                        </Badge>
                        <Badge variant={badgeVariant} size="sm" dot>
                          {item.status} ({item.daysRemaining < 0 ? `${Math.abs(item.daysRemaining)}d ago` : `${item.daysRemaining}d left`})
                        </Badge>
                      </div>
                      <p className="warranty-provider-text">
                        Provider: <strong>{item.provider}</strong> &bull; Duration: {item.duration}
                        {product && product.brand ? ` &bull; Brand: ${product.brand}` : ''}
                      </p>
                    </div>
                  </div>

                  <div className="warranty-dates-box">
                    <div className="date-block">
                      <span className="date-label">Start Date</span>
                      <span className="date-val">{item.startDate}</span>
                    </div>
                    <div className="date-block">
                      <span className="date-label">Expires On</span>
                      <span className={`date-val ${isExpiring ? 'expiry-highlight' : ''}`}>
                        {item.expiryDate || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="warranty-card-sub">
                  <div className="inclusions-pill-row">
                    {item.benefits && item.benefits.length > 0 ? (
                      <>
                        <span className="inclusions-label">Inclusions:</span>
                        {item.benefits.map((inc, i) => (
                          <span key={i} className="inc-tag">✓ {inc}</span>
                        ))}
                      </>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Standard manufacturer terms apply
                      </span>
                    )}
                  </div>
                  <div className="warranty-actions">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/products/${item.productId}`)}
                    >
                      View Product & Claims
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
