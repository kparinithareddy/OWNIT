import React, { useState } from 'react';
import {
  FileText,
  UploadCloud,
  Search,
  Filter,
  Download,
  Eye,
  CheckCircle,
  FileCheck2,
  Plus
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Modal from '../../components/common/Modal';
import Input from '../../components/common/Input';
import { mockDocuments } from '../../data/mockData';
import './Documents.css';

export default function Documents() {
  const [searchTerm, setSearchTerm] = useState('');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const filteredDocs = mockDocuments.filter(
    (doc) =>
      doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <PageContainer
      title="Document Vault"
      subtitle="Safely store, organize, and OCR-parse your purchase receipts, warranty cards, and manuals."
      actions={
        <Button
          variant="primary"
          icon={UploadCloud}
          onClick={() => setIsUploadModalOpen(true)}
        >
          Upload Document / Receipt
        </Button>
      }
    >
      {/* OCR Upload Zone Teaser */}
      <Card className="doc-upload-dropzone" onClick={() => setIsUploadModalOpen(true)}>
        <div className="upload-dropzone-content">
          <div className="upload-icon-circle">
            <UploadCloud size={28} />
          </div>
          <h4 className="upload-dropzone-title">Upload Receipt or Warranty Card</h4>
          <p className="upload-dropzone-subtitle">
            Drag & drop PDF, JPG, PNG files here — Tesseract OCR will automatically extract product metadata
          </p>
          <Button variant="outline" size="sm" style={{ marginTop: '12px' }}>
            Select Files from Computer
          </Button>
        </div>
      </Card>

      {/* Filter and Search */}
      <div className="doc-search-bar">
        <Search size={16} className="doc-search-icon" />
        <input
          type="text"
          placeholder="Search documents by invoice #, product name, or type..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="doc-search-input"
        />
      </div>

      {/* Documents Grid */}
      <div className="documents-grid">
        {filteredDocs.map((doc) => (
          <Card key={doc.id} className="doc-card" padding="md">
            <div className="doc-card-top">
              <span className="doc-thumbnail-emoji">{doc.thumbnail}</span>
              <Badge variant="active" size="sm">
                {doc.ocrStatus}
              </Badge>
            </div>

            <div className="doc-card-body">
              <span className="doc-type-badge">{doc.type}</span>
              <h4 className="doc-card-title">{doc.title}</h4>
              <p className="doc-product-link">Linked to: <strong>{doc.productName}</strong></p>
            </div>

            <div className="doc-card-footer">
              <span className="doc-meta-info">{doc.format} &bull; {doc.size}</span>
              <div className="doc-actions">
                <Button variant="ghost" size="sm" icon={Eye} title="Preview Document">
                  View
                </Button>
                <Button variant="ghost" size="sm" icon={Download} title="Download File">
                  Download
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Upload Modal Placeholder */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Upload Document / Receipt"
        subtitle="Automatic OCR extraction with Tesseract"
      >
        <form onSubmit={(e) => { e.preventDefault(); setIsUploadModalOpen(false); }}>
          <Input label="Document Title" placeholder="e.g. Amazon Tax Invoice #3091" required />
          <Input label="Select File" type="file" required />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
            <Button variant="secondary" onClick={() => setIsUploadModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Process & Save</Button>
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
}
