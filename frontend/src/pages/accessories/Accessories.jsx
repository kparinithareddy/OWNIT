import React from 'react';
import { PlugZap, CheckCircle2, ShoppingBag, ExternalLink } from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import { mockAccessories } from '../../data/mockData';
import './Accessories.css';

export default function Accessories() {
  return (
    <PageContainer
      title="Compatible Accessories & Parts"
      subtitle="Smart recommendations for replacement parts, maintenance filters, and protective gear matched to your registered items."
    >
      <div className="accessories-grid">
        {mockAccessories.map((acc) => (
          <Card key={acc.id} className="accessory-card" padding="md">
            <div className="accessory-top">
              <div className="accessory-icon">
                <PlugZap size={22} />
              </div>
              <Badge variant="info" size="sm">
                {acc.tag}
              </Badge>
            </div>

            <div className="accessory-body">
              <span className="accessory-category">{acc.category}</span>
              <h4 className="accessory-title">{acc.title}</h4>
              <p className="accessory-target">For: <strong>{acc.productName}</strong></p>
              
              <div className="accessory-compat">
                <CheckCircle2 size={14} className="compat-check" />
                <span>{acc.compatibility}</span>
              </div>
            </div>

            <div className="accessory-footer">
              <div>
                <span className="acc-price-label">Price:</span>
                <span className="acc-price-val">{acc.price}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                icon={ShoppingBag}
                onClick={() => alert(`Simulating navigation to ${acc.store}`)}
              >
                Buy at {acc.store}
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </PageContainer>
  );
}
