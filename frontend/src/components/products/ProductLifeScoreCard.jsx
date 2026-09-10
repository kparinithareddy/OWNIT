import React from 'react';
import {
  Activity,
  ShieldCheck,
  FileText,
  Wrench,
  Clock,
  Hash,
  CheckCircle2,
  AlertTriangle,
  Info,
  TrendingUp,
  Sparkles,
  ArrowUpRight
} from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import './ProductLifeScoreCard.css';

function getFactorIcon(name) {
  switch (name) {
    case 'Warranty & Coverage': return ShieldCheck;
    case 'Document Completeness': return FileText;
    case 'Maintenance & Care': return Wrench;
    case 'Product Age': return Clock;
    case 'Asset Identifiers & Records': return Hash;
    default: return Activity;
  }
}

export default function ProductLifeScoreCard({ lifeScore, loading, onActionClick }) {
  if (loading) {
    return (
      <Card title="Product Life Score" subtitle="Computing rule-based asset health...">
        <div className="life-score-loading">
          <div className="score-spinner" />
          <p>Analyzing warranty, documentation, maintenance, and lifecycle factors...</p>
        </div>
      </Card>
    );
  }

  if (!lifeScore) {
    return null;
  }

  const {
    score = 0,
    grade = 'Fair',
    color = 'amber',
    summary = '',
    disclaimer = '',
    factors = [],
    positiveReasons = [],
    improvementTips = []
  } = lifeScore;

  // Grade badge variant
  const badgeVariant = color === 'green' ? 'active' : color === 'amber' ? 'warning' : 'danger';

  // Compute stroke offset for circular gauge
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <Card
      title="Product Life Score"
      subtitle="Transparent rule-based assessment of coverage, documentation, and maintenance"
      className="product-life-score-card"
    >
      {/* Top Hero Section: Circular Gauge + Summary */}
      <div className="score-hero-section">
        {/* Circular Gauge */}
        <div className="score-gauge-container">
          <svg className="score-gauge-svg" width="110" height="110" viewBox="0 0 100 100">
            {/* Background Track */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              className="gauge-bg"
            />
            {/* Progress Arc */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              className={`gauge-progress ${color}`}
              style={{
                strokeDasharray: circumference,
                strokeDashoffset: strokeDashoffset
              }}
            />
          </svg>
          <div className="gauge-center-text">
            <span className="gauge-number">{score}</span>
            <span className="gauge-max">/100</span>
          </div>
        </div>

        {/* Score Overview & Classification */}
        <div className="score-summary-content">
          <div className="score-header-pill-row">
            <h3 className="score-title">Asset Health Score</h3>
            <Badge variant={badgeVariant} size="md" dot>
              {grade}
            </Badge>
          </div>
          <p className="score-summary-text">{summary}</p>
          <div className="score-sub-meta">
            <span className="score-meta-item">
              <TrendingUp size={14} color="var(--primary)" /> 5 Assessment Dimensions
            </span>
            <span className="score-meta-item">
              <Sparkles size={14} color="var(--amber)" /> Real-time Calculation
            </span>
          </div>
        </div>
      </div>

      {/* Breakdown by Dimension */}
      <div className="score-factors-section">
        <h4 className="factors-heading">Contributing Factor Breakdown</h4>
        <div className="factors-grid">
          {factors.map((factor, idx) => {
            const Icon = getFactorIcon(factor.name);
            const factorPercent = Math.round((factor.score / factor.maxScore) * 100);
            const statusClass = factor.status === 'positive' ? 'status-pos' : factor.status === 'warning' ? 'status-warn' : 'status-neg';

            return (
              <div key={idx} className={`factor-item-card ${statusClass}`}>
                <div className="factor-item-top">
                  <div className="factor-title-wrap">
                    <Icon size={16} className="factor-icon" />
                    <span className="factor-name">{factor.name}</span>
                  </div>
                  <span className="factor-score-pill">
                    <strong>{factor.score}</strong> / {factor.maxScore} pts
                  </span>
                </div>

                <div className="factor-progress-bar">
                  <div
                    className={`factor-progress-fill ${statusClass}`}
                    style={{ width: `${factorPercent}%` }}
                  />
                </div>

                <p className="factor-desc">{factor.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Explanations & Improvement Recommendations */}
      <div className="score-details-2col">
        {/* Positive Reasons */}
        <div className="reasons-box positive-box">
          <h5 className="reasons-title">
            <CheckCircle2 size={16} color="var(--success)" /> Why this score?
          </h5>
          {positiveReasons.length === 0 ? (
            <p className="reasons-empty">No positive factors registered yet.</p>
          ) : (
            <ul className="reasons-list">
              {positiveReasons.map((reason, idx) => (
                <li key={idx} className="reason-item">
                  <span className="reason-bullet">✓</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Actionable Improvement Tips */}
        <div className="reasons-box tips-box">
          <h5 className="reasons-title">
            <ArrowUpRight size={16} color="var(--primary)" /> Ways to Improve Score
          </h5>
          {improvementTips.length === 0 ? (
            <p className="reasons-empty">All records in optimal standing! No immediate actions required.</p>
          ) : (
            <ul className="reasons-list">
              {improvementTips.map((tip, idx) => (
                <li key={idx} className="reason-item tip-item">
                  <span className="tip-bullet">→</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Mandatory Non-Predictive Disclaimer */}
      <div className="score-disclaimer-banner">
        <Info size={15} className="disclaimer-icon" />
        <span className="disclaimer-text">
          <strong>Transparency Notice:</strong> {disclaimer}
        </span>
      </div>
    </Card>
  );
}
