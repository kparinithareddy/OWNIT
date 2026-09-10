import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  Plus,
  Search,
  Filter,
  ShieldCheck,
  Calendar,
  DollarSign,
  ArrowUpRight
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import EmptyState from '../../components/common/EmptyState';
import Modal from '../../components/common/Modal';
import Input, { Select } from '../../components/common/Input';
import { mockProducts } from '../../data/mockData';
import './ProductList.css';

export default function ProductList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const filteredProducts = mockProducts.filter((product) => {
    const matchesSearch =
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.brand.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.model.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === 'All' || product.category === selectedCategory;

    const matchesStatus =
      selectedStatus === 'All' || product.warrantyStatus === selectedStatus;

    return matchesSearch && matchesCategory && matchesStatus;
  });

  const categories = ['All', 'Electronics', 'Audio', 'Home Appliances'];

  return (
    <PageContainer
      title="Products & Assets"
      subtitle="View, manage, and track all your registered physical purchases and their warranties."
      actions={
        <Button
          variant="primary"
          icon={Plus}
          onClick={() => setIsModalOpen(true)}
        >
          Add Product
        </Button>
      }
    >
      {/* Search & Filter Bar */}
      <div className="product-filter-bar">
        <div className="product-search-box">
          <Search size={16} className="product-search-icon" />
          <input
            type="text"
            placeholder="Search by product name, brand, or model..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="product-search-input"
          />
        </div>

        <div className="product-filters">
          <div className="filter-group">
            <span className="filter-label">Category:</span>
            <div className="filter-pills">
              {categories.map((cat) => (
                <button
                  key={cat}
                  className={`filter-pill ${selectedCategory === cat ? 'filter-pill-active' : ''}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-group">
            <span className="filter-label">Status:</span>
            <select
              className="filter-select"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              <option value="All">All Statuses</option>
              <option value="active">Active Warranty</option>
              <option value="expiring">Expiring Soon</option>
              <option value="expired">Expired</option>
            </select>
          </div>
        </div>
      </div>

      {/* Product Cards Grid */}
      {filteredProducts.length > 0 ? (
        <div className="product-grid">
          {filteredProducts.map((product) => (
            <Card
              key={product.id}
              hoverable
              className="product-card"
              onClick={() => navigate(`/products/${product.id}`)}
            >
              <div className="product-card-top">
                <div className="product-avatar">
                  <Package size={24} />
                </div>
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

              <div className="product-card-info">
                <span className="product-brand-tag">{product.brand}</span>
                <h3 className="product-title">{product.name}</h3>
                <p className="product-model">{product.model}</p>
              </div>

              <div className="product-card-meta">
                <div className="product-meta-item">
                  <Calendar size={14} />
                  <span>Purchased: {product.purchaseDate}</span>
                </div>
                <div className="product-meta-item">
                  <ShieldCheck size={14} />
                  <span>Warranty: {product.warrantyExpiry}</span>
                </div>
              </div>

              <div className="product-card-footer">
                <div className="product-price">{product.purchasePrice}</div>
                <div className="product-life-score" title="Product Life Score">
                  <span className="life-score-label">Life Score:</span>
                  <span className="life-score-val">{product.lifeScore}%</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No products match your search"
          description="Try adjusting your search filters or add a new product."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearchTerm('');
            setSelectedCategory('All');
            setSelectedStatus('All');
          }}
        />
      )}

      {/* Add Product Modal Placeholder */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Product to Catalog"
        subtitle="Enter product invoice details manually"
      >
        <form onSubmit={(e) => { e.preventDefault(); setIsModalOpen(false); }}>
          <Input label="Product Name" placeholder="e.g. Sony WH-1000XM5" required />
          <Input label="Brand" placeholder="e.g. Sony" required />
          <Input label="Purchase Date" type="date" required />
          <Input label="Purchase Price" placeholder="₹24,990" />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Save Product</Button>
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
}
