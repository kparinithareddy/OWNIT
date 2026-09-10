import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Package,
  ShieldCheck,
  Calendar,
  DollarSign,
  Store,
  FileText,
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  Wrench,
  Bot
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import { mockProducts } from '../../data/mockData';
import './ProductDetail.css';

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'warranty' | 'lifecycle' | 'documents'

  const product = mockProducts.find((p) => p.id === id) || mockProducts[0];

  return (
    <PageContainer
      badge={
        <Link to="/products" className="back-link">
          <ArrowLeft size={14} /> Back to Products
        </Link>
      }
      title={product.name}
      subtitle={`${product.brand} • Serial: ${product.serialNumber}`}
      actions={
        <div className="product-detail-actions">
          <Button
            variant="outline"
            icon={Bot}
            onClick={() => navigate('/ai-assistant')}
          >
            Ask AI About This
          </Button>
          <Button variant="primary" icon={FileText} onClick={() => navigate('/documents')}>
            View Invoices
          </Button>
        </div>
      }
    >
      {/* Product Overview Header Card */}
      <Card className="product-hero-card" padding="lg">
        <div className="hero-grid">
          <div className="hero-left">
            <div className="hero-avatar">
              <Package size={36} />
            </div>
            <div className="hero-info">
              <span className="hero-category">{product.category}</span>
              <h2 className="hero-title">{product.name}</h2>
              <p className="hero-model">{product.model}</p>
              <p className="hero-desc">{product.description}</p>
            </div>
          </div>

          <div className="hero-right">
            <div className="life-score-badge-card">
              <span className="life-score-num">{product.lifeScore}</span>
              <span className="life-score-denom">/ 100</span>
              <p className="life-score-title">Product Life Score</p>
              <span className="life-score-status">Excellent Health</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs Navigation */}
      <div className="product-detail-tabs">
        <button
          className={`detail-tab ${activeTab === 'overview' ? 'detail-tab-active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Product Specs
        </button>
        <button
          className={`detail-tab ${activeTab === 'warranty' ? 'detail-tab-active' : ''}`}
          onClick={() => setActiveTab('warranty')}
        >
          Warranty & Return Policy
        </button>
        <button
          className={`detail-tab ${activeTab === 'lifecycle' ? 'detail-tab-active' : ''}`}
          onClick={() => setActiveTab('lifecycle')}
        >
          Lifecycle Timeline
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="tab-grid-2col">
          <Card title="Purchase & Asset Details">
            <div className="detail-meta-list">
              <div className="detail-meta-row">
                <span className="meta-label"><Store size={14} /> Store / Vendor:</span>
                <span className="meta-val">{product.store}</span>
              </div>
              <div className="detail-meta-row">
                <span className="meta-label"><Calendar size={14} /> Purchase Date:</span>
                <span className="meta-val">{product.purchaseDate}</span>
              </div>
              <div className="detail-meta-row">
                <span className="meta-label"><DollarSign size={14} /> Purchase Price:</span>
                <span className="meta-val">{product.purchasePrice}</span>
              </div>
              <div className="detail-meta-row">
                <span className="meta-label"><Clock size={14} /> Return Period Ended:</span>
                <span className="meta-val">{product.returnPeriodExpiry}</span>
              </div>
            </div>
          </Card>

          <Card title="Document Status">
            <div className="document-checks-list">
              <div className="doc-check-row">
                <div className="doc-check-icon doc-check-pass">
                  <CheckCircle2 size={16} />
                </div>
                <div>
                  <strong>Original Tax Invoice (PDF)</strong>
                  <p className="doc-check-sub">Verified by OCR &bull; Ready for claims</p>
                </div>
              </div>
              <div className="doc-check-row">
                <div className="doc-check-icon doc-check-pass">
                  <CheckCircle2 size={16} />
                </div>
                <div>
                  <strong>Warranty Certificate</strong>
                  <p className="doc-check-sub">Uploaded and indexed</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'warranty' && (
        <div className="tab-grid-2col">
          <Card title="Warranty Inclusions & Benefits">
            <ul className="warranty-points-list inclusions">
              {product.warrantyDetails.inclusions.map((item, idx) => (
                <li key={idx} className="warranty-point-item">
                  <CheckCircle2 size={16} className="text-success" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card title="Warranty Exclusions (Not Covered)">
            <ul className="warranty-points-list exclusions">
              {product.warrantyDetails.exclusions.map((item, idx) => (
                <li key={idx} className="warranty-point-item">
                  <XCircle size={16} className="text-danger" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      {activeTab === 'lifecycle' && (
        <Card title="Product Lifecycle & Maintenance Timeline">
          <div className="timeline-container">
            {product.maintenanceHistory.map((event, idx) => (
              <div key={idx} className="timeline-item">
                <div className="timeline-dot" />
                <div className="timeline-content">
                  <span className="timeline-date">{event.date}</span>
                  <h4 className="timeline-title">{event.title}</h4>
                  <p className="timeline-type">Category: {event.type}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </PageContainer>
  );
}
