import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  ShieldCheck,
  ExternalLink,
  RefreshCw,
  Info,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  HelpCircle,
  Globe
} from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { recallsApi } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';
import './SafetyRecallCard.css';

export default function SafetyRecallCard({ product, productId }) {
  const { t } = useLanguage();
  const targetId = productId || product?.id;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRecallStatus = async () => {
    if (!targetId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await recallsApi.checkProduct(targetId);
      setData(res);
    } catch (err) {
      console.error('Failed to fetch safety recall status:', err);
      setError(err.message || 'Unable to scan safety recall bulletins');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecallStatus();
  }, [targetId]);

  if (!targetId) return null;

  const getSeverityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return <Badge variant="danger" icon={AlertOctagon}>CRITICAL SAFETY</Badge>;
      case 'WARNING':
        return <Badge variant="warning" icon={AlertTriangle}>WARNING</Badge>;
      default:
        return <Badge variant="info" icon={Info}>ADVISORY</Badge>;
    }
  };

  const getSerialStatusBadge = (isSerialMatched) => {
    if (isSerialMatched === true) {
      return (
        <span className="recall-serial-tag matched">
          <AlertTriangle size={13} />
          {t('recalls.serialMatched') || 'Serial Number Matched'}
        </span>
      );
    }
    if (isSerialMatched === false) {
      return (
        <span className="recall-serial-tag not-matched">
          <CheckCircle2 size={13} />
          {t('recalls.serialNotMatched') || 'Serial Not in Range'}
        </span>
      );
    }
    return (
      <span className="recall-serial-tag unverified">
        <HelpCircle size={13} />
        {t('recalls.serialUnverified') || 'Serial Unverified'}
      </span>
    );
  };

  return (
    <Card className="safety-recall-card">
      <div className="safety-recall-header">
        <div className="safety-recall-title-group">
          <div className="safety-recall-icon-wrap">
            {data?.hasPossibleRecall ? (
              <AlertTriangle className="text-warning-icon" size={22} />
            ) : (
              <ShieldCheck className="text-success-icon" size={22} />
            )}
          </div>
          <div>
            <h3 className="safety-recall-title">{t('recalls.title') || 'Safety Recalls & Bulletins'}</h3>
            <p className="safety-recall-subtitle">
              {t('recalls.subtitle') || 'Cross-referenced against verified manufacturer safety programs and official regulatory databases.'}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchRecallStatus}
          disabled={loading}
          icon={<RefreshCw size={14} className={loading ? 'animate-spin' : ''} />}
        >
          {loading ? (t('common.loading') || 'Checking...') : (t('common.retry') || 'Recheck')}
        </Button>
      </div>

      {loading && !data && (
        <div className="safety-recall-loading">
          <RefreshCw size={24} className="animate-spin text-primary" />
          <p>{t('common.loading') || 'Scanning verified safety bulletins...'}</p>
        </div>
      )}

      {error && !loading && (
        <div className="safety-recall-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
          <Button size="xs" variant="outline" onClick={fetchRecallStatus}>
            {t('common.retry') || 'Retry'}
          </Button>
        </div>
      )}

      {data && !loading && (
        <div className="safety-recall-content">
          {data.hasPossibleRecall ? (
            <div className="safety-recall-alerts-container">
              {/* Mandatory Advisory Notice */}
              <div className="safety-recall-warning-banner">
                <AlertTriangle size={20} className="warning-banner-icon" />
                <div className="warning-banner-body">
                  <div className="warning-banner-title">
                    {data.warningMessage || 'Possible recall match — verify with the official source.'}
                  </div>
                  <div className="warning-banner-meta">
                    {t('recalls.disclaimer') || 'Advisory notice based on published manufacturer bulletins. Always verify eligibility with the official manufacturer source.'}
                  </div>
                </div>
              </div>

              {/* Matched Recall Programs */}
              <div className="safety-recall-matches-list">
                {data.matches?.map((match) => (
                  <div key={match.recallId} className={`recall-match-card severity-${match.severity?.toLowerCase()}`}>
                    <div className="recall-match-header">
                      <div className="recall-match-header-left">
                        {getSeverityBadge(match.severity)}
                        <h4 className="recall-match-title">{match.title}</h4>
                      </div>
                      {getSerialStatusBadge(match.isSerialMatched)}
                    </div>

                    <div className="recall-match-grid">
                      <div className="recall-detail-block">
                        <span className="recall-detail-label">{t('recalls.affectedModel') || 'Affected Model'}</span>
                        <span className="recall-detail-value">{match.affectedBrand} {match.affectedModel}</span>
                      </div>

                      {match.affectedSerialRange && (
                        <div className="recall-detail-block full-width">
                          <span className="recall-detail-label">{t('recalls.serialRange') || 'Affected Range / Batches'}</span>
                          <span className="recall-detail-value">{match.affectedSerialRange}</span>
                        </div>
                      )}

                      <div className="recall-detail-block full-width hazard-box">
                        <span className="recall-detail-label">{t('recalls.hazard') || 'Potential Safety Hazard'}</span>
                        <p className="recall-hazard-text">{match.hazard}</p>
                      </div>

                      <div className="recall-detail-block full-width action-box">
                        <span className="recall-detail-label">{t('recalls.recommendedAction') || 'Recommended Action'}</span>
                        <div className="recall-action-text">
                          {match.recommendedAction.split('\n').map((step, idx) => (
                            <div key={idx} className="recall-action-step">{step}</div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="recall-match-footer">
                      <div className="recall-source-info">
                        <Globe size={14} />
                        <span>{t('recalls.officialSource') || 'Source'}: <strong>{match.officialSource}</strong> ({match.sourceDomain})</span>
                      </div>
                      {match.sourceUrl && (
                        <a
                          href={match.sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="recall-verify-link"
                        >
                          <span>{t('recalls.verifyWithSource') || 'Verify on Official Source'}</span>
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="safety-recall-clean-state">
              <div className="clean-state-icon">
                <ShieldCheck size={32} />
              </div>
              <div className="clean-state-text">
                <h4>{t('recalls.noRecallsFound') || 'No Active Recalls Found'}</h4>
                <p>{t('recalls.cleanDescription') || 'No manufacturer safety bulletins or recall notices found for this model.'}</p>
                <span className="clean-checked-at">
                  {t('common.status') || 'Status'}: Verified against official registries • {new Date(data.checkedAt).toLocaleDateString()}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
