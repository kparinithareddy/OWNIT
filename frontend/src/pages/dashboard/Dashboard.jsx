import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  ShieldCheck,
  Clock,
  Sparkles,
  Camera,
  Plus,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  FileText,
  Smartphone,
  Laptop,
  Tv,
  Volume2
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card, { StatCard } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Modal from '../../components/common/Modal';
import LoadingState from '../../components/common/LoadingState';
import ProductFormModal from '../../components/products/ProductFormModal';
import { productsApi } from '../../services/api';
import { mockNotifications } from '../../data/mockData';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data = await productsApi.list();
      setProducts(data);
    } catch (err) {
      console.warn('Could not load products on dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const totalValue = products.reduce((acc, p) => acc + (p.price * (p.quantity || 1)), 0);

  return (
    <PageContainer
      title="Dashboard Overview"
      subtitle="Track your products, active warranties, and upcoming expiration deadlines."
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
      {/* Stat Cards Grid */}
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
          value={loading ? '...' : String(products.length > 0 ? products.length : 0)}
          subtitle="Protected devices"
          icon={ShieldCheck}
          variant="success"
        />
        <StatCard
          title="Expiring Soon"
          value="0"
          subtitle="Within next 30 days"
          icon={Clock}
          variant="warning"
        />
        <StatCard
          title="AI Assistant"
          value="Ready"
          subtitle="Local Ollama Engine"
          icon={Sparkles}
          variant="info"
        />
      </div>

      {/* Main 2-Column Section */}
      <div className="dashboard-main-grid">
        {/* Left Column: Recent Products */}
        <div className="dashboard-col-left">
          <Card
            title="My Registered Products"
            subtitle="Your cataloged physical items and electronics"
            action={
              <Button
                variant="ghost"
                size="sm"
                icon={ArrowRight}
                iconPosition="right"
                onClick={() => navigate('/products')}
              >
                View All ({products.length})
              </Button>
            }
          >
            {loading ? (
              <LoadingState message="Loading products..." description="" />
            ) : products.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                <Package size={36} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  No products added yet
                </h4>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '4px', marginBottom: '16px' }}>
                  Click below to add your first physical product!
                </p>
                <Button variant="primary" size="sm" icon={Plus} onClick={() => setIsAddModalOpen(true)}>
                  Add Product Now
                </Button>
              </div>
            ) : (
              <div className="dashboard-product-list">
                {products.slice(0, 5).map((product) => (
                  <div
                    key={product.id}
                    className="dashboard-product-row"
                    onClick={() => navigate(`/products/${product.id}`)}
                  >
                    <div className="product-row-icon">
                      <Package size={20} />
                    </div>
                    <div className="product-row-info">
                      <h4 className="product-row-name">{product.name}</h4>
                      <p className="product-row-details">
                        {product.brand} &bull; {product.category} &bull; ₹{product.price.toLocaleString('en-IN')}
                      </p>
                    </div>
                    <div className="product-row-status">
                      <Badge variant="info" size="sm">
                        {product.category}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Alerts & AI Recommendations */}
        <div className="dashboard-col-right">
          <Card
            title="Priority Alerts & Reminders"
            subtitle="Upcoming warranty deadlines & maintenance tasks"
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/notifications')}
              >
                All Alerts
              </Button>
            }
          >
            <div className="dashboard-alerts-list">
              {mockNotifications.map((notif) => (
                <div key={notif.id} className={`dashboard-alert-item alert-type-${notif.type}`}>
                  <div className="alert-item-icon">
                    {notif.type === 'warning' && <AlertTriangle size={18} />}
                    {notif.type === 'info' && <Clock size={18} />}
                    {notif.type === 'success' && <CheckCircle size={18} />}
                  </div>
                  <div className="alert-item-content">
                    <h5 className="alert-item-title">{notif.title}</h5>
                    <p className="alert-item-message">{notif.message}</p>
                    <span className="alert-item-time">{notif.date}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Quick AI Prompt Card */}
          <Card className="dashboard-ai-card" padding="md">
            <div className="ai-banner-content">
              <div className="ai-banner-badge">
                <Sparkles size={14} />
                <span>Local AI Ready</span>
              </div>
              <h4 className="ai-banner-title">Ask OWNIT Assistant</h4>
              <p className="ai-banner-desc">
                Have questions about warranty coverage, claim letters, or manuals?
              </p>
              <Button
                variant="primary"
                size="sm"
                icon={Sparkles}
                onClick={() => navigate('/ai-assistant')}
              >
                Open AI Assistant
              </Button>
            </div>
          </Card>
        </div>
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
            Supports PDF, PNG, JPG (Processed completely locally with Tesseract)
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
