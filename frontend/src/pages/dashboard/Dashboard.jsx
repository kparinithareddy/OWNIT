import React, { useState } from 'react';
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
  FileText
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card, { StatCard } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Modal from '../../components/common/Modal';
import Input, { Select } from '../../components/common/Input';
import { mockProducts, mockNotifications } from '../../data/mockData';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);

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
          value="5"
          subtitle="All registered assets"
          icon={Package}
          variant="primary"
        />
        <StatCard
          title="Active Warranties"
          value="3"
          subtitle="Fully covered items"
          icon={ShieldCheck}
          variant="success"
        />
        <StatCard
          title="Expiring Soon"
          value="1"
          subtitle="Within next 30 days"
          icon={Clock}
          variant="warning"
        />
        <StatCard
          title="AI Assistant"
          value="Ready"
          subtitle="Local Ollama LLaMA"
          icon={Sparkles}
          variant="info"
        />
      </div>

      {/* Main 2-Column Section */}
      <div className="dashboard-main-grid">
        {/* Left Column: Recent Products */}
        <div className="dashboard-col-left">
          <Card
            title="Recent Products"
            subtitle="Your registered devices and their current lifecycle status"
            action={
              <Button
                variant="ghost"
                size="sm"
                icon={ArrowRight}
                iconPosition="right"
                onClick={() => navigate('/products')}
              >
                View All
              </Button>
            }
          >
            <div className="dashboard-product-list">
              {mockProducts.slice(0, 4).map((product) => (
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
                      {product.brand} &bull; Purchased: {product.purchaseDate}
                    </p>
                  </div>
                  <div className="product-row-status">
                    <Badge
                      variant={
                        product.warrantyStatus === 'active'
                          ? 'active'
                          : product.warrantyStatus === 'expiring'
                          ? 'warning'
                          : 'danger'
                      }
                      dot
                    >
                      {product.warrantyStatus === 'active'
                        ? 'Active Warranty'
                        : product.warrantyStatus === 'expiring'
                        ? 'Expiring Soon'
                        : 'Expired'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
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

      {/* Placeholder Modal: Add Product */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add New Product (Placeholder)"
        subtitle="Catalog a new purchase manually into OWNIT"
      >
        <form onSubmit={(e) => { e.preventDefault(); setIsAddModalOpen(false); }}>
          <Input label="Product Name" placeholder="e.g. Sony WH-1000XM5 Headphones" required />
          <Input label="Brand / Manufacturer" placeholder="e.g. Sony" required />
          <Input label="Serial Number" placeholder="e.g. S01-8492048-A" />
          <Input label="Purchase Date" type="date" required />
          <Input label="Purchase Price (₹)" placeholder="e.g. 24990" />
          <Select
            label="Category"
            options={[
              { value: 'electronics', label: 'Electronics' },
              { value: 'appliances', label: 'Home Appliances' },
              { value: 'audio', label: 'Audio & Wearables' },
              { value: 'other', label: 'Other' }
            ]}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
            <Button variant="secondary" onClick={() => setIsAddModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Save Product</Button>
          </div>
        </form>
      </Modal>

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
