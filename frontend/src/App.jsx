import React, { useEffect, useState } from 'react'
import './App.css'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [backendData, setBackendData] = useState(null)

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    
    fetch(`${apiUrl}/api/health`)
      .then((res) => {
        if (res.ok) return res.json()
        throw new Error('Backend response not OK')
      })
      .then((data) => {
        setApiStatus('connected')
        setBackendData(data)
      })
      .catch(() => {
        setApiStatus('disconnected')
      })
  }, [])

  return (
    <div className="container">
      <header className="header">
        <div className="badge">
          <span>🛡️</span> Project Initialized
        </div>
        <h1 className="title">OWNIT</h1>
        <p className="tagline">"Own More. Worry Less."</p>
      </header>

      <main>
        <section className="card">
          <h2 className="card-title">System Status</h2>
          <div className="status-grid">
            <div className="status-card">
              <div className="status-header">
                <span className="status-name">Frontend (React + Vite)</span>
                <span className="status-badge status-ready">Active</span>
              </div>
              <p className="status-desc">Web client running on port 5173</p>
            </div>

            <div className="status-card">
              <div className="status-header">
                <span className="status-name">Backend API (FastAPI)</span>
                <span className={`status-badge ${apiStatus === 'connected' ? 'status-ready' : ''}`}>
                  {apiStatus === 'connected' ? 'Connected' : apiStatus === 'checking' ? 'Checking...' : 'Offline'}
                </span>
              </div>
              <p className="status-desc">
                {apiStatus === 'connected' && backendData
                  ? `v${backendData.version} (${backendData.environment})`
                  : 'Start backend with: uvicorn main:app --reload'}
              </p>
            </div>

            <div className="status-card">
              <div className="status-header">
                <span className="status-name">Monorepo Structure</span>
                <span className="status-badge status-ready">Ready</span>
              </div>
              <p className="status-desc">frontend/, backend/, and docs/ initialized</p>
            </div>
          </div>
        </section>

        <section className="card">
          <h2 className="card-title">Next Implementation Modules</h2>
          <ul className="next-steps">
            <li className="step-item">
              <span className="step-number">1</span>
              <div>
                <strong>Database & User Authentication</strong>
                <p className="status-desc">MongoDB schema setup and JWT-based authentication</p>
              </div>
            </li>
            <li className="step-item">
              <span className="step-number">2</span>
              <div>
                <strong>Product & Document Management</strong>
                <p className="status-desc">Cataloging physical items, receipts, and user warranty documents</p>
              </div>
            </li>
            <li className="step-item">
              <span className="step-number">3</span>
              <div>
                <strong>OCR Engine & AI Assistant</strong>
                <p className="status-desc">Tesseract receipt extraction and local Ollama intelligence</p>
              </div>
            </li>
          </ul>
        </section>
      </main>

      <footer className="footer">
        <p>OWNIT — Smart Product Lifecycle Assistant &bull; Initial Foundation</p>
      </footer>
    </div>
  )
}
