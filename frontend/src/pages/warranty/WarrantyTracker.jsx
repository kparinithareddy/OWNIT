import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Bot,
  ExternalLink,
  HelpCircle
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card, { StatCard } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import { mockProducts } from '../../data/mockData';
import './WarrantyTracker.css';

export default function WarrantyTracker() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('all'); // 'all' | 'active' | 'expiring' | 'expired'

  const filteredItems = mockProducts.filter((item) => {
    if (filter === 'all') return true;
    return item.warrantyStatus === filter;
  });

  return (
    <PageContainer
      title="Warranty & Return Tracker"
      subtitle="Monitor coverage validity, return deadlines, and claim eligibility across all purchases."
      actions={
        <Button
          variant="outline"
          icon={Bot}
          onClick={() => navigate('/ai-assistant')}
        >
          Analyze Coverage with AI
        </Button>
      }
    >
      {/* Metric Cards */}
      <div className="warranty-stats-grid">
        <StatCard
          title="Active Warranties"
          value="3 Products"
          subtitle="100% Eligible for free repair"
          icon={ShieldCheck}
          variant="success"
        />
        <StatCard
          title="Expiring Within 30 Days"
          value="1 Product"
          subtitle="Sony WH-1000XM5"
          icon={ShieldAlert}
          variant="warning"
        />
        <StatCard
          title="Expired / Out of Coverage"
          value="1 Product"
          subtitle="LG OLED 55 TV"
          icon={Clock}
          variant="danger"
        />
      </div>

      {/* Filter Tabs */}
      <div className="warranty-filters">
        <button
          className={`warranty-filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Items ({mockProducts.length})
        </button>
        <button
          className={`warranty-filter-btn ${filter === 'active' ? 'active' : ''}`}
          onClick={() => setFilter('active')}
        >
          Active Coverage
        </button>
        <button
          className={`warranty-filter-btn ${filter === 'expiring' ? 'active' : ''}`}
          onClick={() => setFilter('expiring')}
        >
          Expiring Soon ⚠️
        </button>
        <button
          className={`warranty-filter-btn ${filter === 'expired' ? 'active' : ''}`}
          onClick={() => setFilter('expired')}
        >
          Expired
        </button>
      </div>

      {/* Warranty List */}
      <div className="warranty-cards-list">
        {filteredItems.map((item) => (
          <Card key={item.id} className="warranty-card" padding="md">
            <div className="warranty-card-main">
              <div className="warranty-card-left">
                <div className="warranty-avatar">
                  <ShieldCheck size={24} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 className="warranty-prod-title">{item.name}</h3>
                    <Badge
                      variant={
                        item.warrantyStatus === 'active'
                          ? 'active'
                          : item.warrantyStatus === 'expiring'
                          ? 'warning'
                          : 'danger'
                      }
                      size="sm"
                      dot
                    >
                      {item.warrantyStatus === 'active'
                        ? 'Active'
                        : item.warrantyStatus === 'expiring'
                        ? 'Expiring in 14 days'
                        : 'Expired'}
                    </Badge>
                  </div>
                  <p className="warranty-provider-text">
                    Provider: <strong>{item.warrantyDetails.provider}</strong> &bull; Serial: {item.serialNumber}
                  </p>
                </div>
              </div>

              <div className="warranty-dates-box">
                <div className="date-block">
                  <span className="date-label">Start Date</span>
                  <span className="date-val">{item.purchaseDate}</span>
                </div>
                <div className="date-block">
                  <span className="date-label">Expires On</span>
                  <span className="date-val expiry-highlight">{item.warrantyExpiry}</span>
                </div>
              </div>
            </div>

            <div className="warranty-card-sub">
              <div className="inclusions-pill-row">
                <span className="inclusions-label">Covered:</span>
                {item.warrantyDetails.inclusions.map((inc, i) => (
                  <span key={i} className="inc-tag">{inc}</span>
                ))}
              </div>
              <div className="warranty-actions">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/products/${item.id}`)}
                >
                  View Details
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  icon={Bot}
                  onClick={() => navigate('/ai-assistant')}
                >
                  Claim Assistant
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </PageContainer>
  );
}
