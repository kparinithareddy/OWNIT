import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  Check,
  RefreshCw,
  ArrowRight,
  ExternalLink,
  Sparkles,
  Inbox
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import { notificationsApi } from '../../services/api';
import './Notifications.css';

function getNotificationVisuals(type) {
  switch (type) {
    case 'WARRANTY_EXPIRY_0D':
      return {
        icon: ShieldAlert,
        variant: 'danger',
        label: 'Coverage Ended',
        iconClass: 'notif-icon-danger'
      };
    case 'WARRANTY_EXPIRY_1D':
      return {
        icon: AlertTriangle,
        variant: 'danger',
        label: 'Expires Tomorrow',
        iconClass: 'notif-icon-danger'
      };
    case 'WARRANTY_EXPIRY_7D':
      return {
        icon: AlertTriangle,
        variant: 'warning',
        label: 'Expires in 7 Days',
        iconClass: 'notif-icon-warning'
      };
    case 'WARRANTY_EXPIRY_15D':
      return {
        icon: Clock,
        variant: 'warning',
        label: 'Expires in 15 Days',
        iconClass: 'notif-icon-warning'
      };
    case 'WARRANTY_EXPIRY_30D':
      return {
        icon: ShieldCheck,
        variant: 'info',
        label: 'Expires in 30 Days',
        iconClass: 'notif-icon-info'
      };
    default:
      return {
        icon: Bell,
        variant: 'neutral',
        label: 'Alert',
        iconClass: 'notif-icon-info'
      };
  }
}

export default function Notifications() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState(null);

  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await notificationsApi.list({ unreadOnly });
      setNotifications(data);
    } catch (err) {
      console.error('Error loading notifications:', err);
      setError(err.message || 'Failed to fetch notification history.');
    } finally {
      setLoading(false);
    }
  }, [unreadOnly]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
    } catch (err) {
      alert(`Could not mark all as read: ${err.message}`);
    }
  };

  const handleMarkAsRead = async (id, e) => {
    e.stopPropagation();
    try {
      await notificationsApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
      );
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await notificationsApi.delete(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      alert(`Failed to delete notification: ${err.message}`);
    }
  };

  const handleTriggerCheck = async () => {
    try {
      setIsChecking(true);
      const result = await notificationsApi.triggerCheck();
      alert(`Evaluation complete: Evaluated ${result.evaluatedWarranties} warranties, created ${result.newNotificationsCreated} new notification(s).`);
      fetchNotifications();
    } catch (err) {
      alert(`Failed to trigger check: ${err.message}`);
    } finally {
      setIsChecking(false);
    }
  };

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <PageContainer
      title="Notifications & Warranty Reminders"
      subtitle="Automated countdowns for 30d, 15d, 7d, 1d, and expiry milestones across all your registered products."
      actions={
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <Button
            variant="outline"
            icon={RefreshCw}
            disabled={isChecking}
            onClick={handleTriggerCheck}
          >
            {isChecking ? 'Checking...' : 'Check Expiry Now'}
          </Button>
          <Button
            variant="outline"
            icon={Check}
            disabled={unreadCount === 0}
            onClick={handleMarkAllAsRead}
          >
            Mark All as Read
          </Button>
        </div>
      }
    >
      {/* Filter Tabs */}
      <div className="notif-filter-bar">
        <button
          className={`notif-tab-btn ${!unreadOnly ? 'active' : ''}`}
          onClick={() => setUnreadOnly(false)}
        >
          All Notifications ({notifications.length})
        </button>
        <button
          className={`notif-tab-btn ${unreadOnly ? 'active' : ''}`}
          onClick={() => setUnreadOnly(true)}
        >
          Unread Only {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>

      {loading ? (
        <LoadingState message="Loading notifications..." description="Checking warranty reminders..." />
      ) : error ? (
        <Card>
          <div style={{ padding: '16px', color: 'var(--danger)' }}>{error}</div>
        </Card>
      ) : notifications.length === 0 ? (
        <Card>
          <div className="notif-empty-box">
            <Inbox size={40} style={{ color: 'var(--text-light)', marginBottom: '8px' }} />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>
              {unreadOnly ? 'No unread notifications' : 'No notifications yet'}
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '4px auto 16px' }}>
              When your products approach their 30-day, 15-day, 7-day, or 1-day warranty milestones, automated in-app alerts will be displayed here.
            </p>
            <Button variant="outline" size="sm" onClick={() => navigate('/products')}>
              Manage Registered Products
            </Button>
          </div>
        </Card>
      ) : (
        <div className="notifications-container">
          {notifications.map((notif) => {
            const visuals = getNotificationVisuals(notif.type);
            const IconComp = visuals.icon;

            return (
              <Card
                key={notif.id}
                className={`notif-card ${!notif.isRead ? 'notif-unread' : ''}`}
                padding="md"
              >
                <div className="notif-row">
                  <div className={`notif-icon-box ${visuals.iconClass}`}>
                    <IconComp size={20} />
                  </div>

                  <div className="notif-content">
                    <div className="notif-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <span className="notif-title">Warranty Alert</span>
                        <Badge variant={visuals.variant} size="sm">
                          {visuals.label}
                        </Badge>
                        {!notif.isRead && (
                          <span className="unread-pill">Unread</span>
                        )}
                      </div>
                      <span className="notif-time">
                        {new Date(notif.createdAt).toLocaleDateString()} at{' '}
                        {new Date(notif.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <p className="notif-message">{notif.message}</p>

                    <div className="notif-actions-row">
                      {notif.productId && (
                        <Button
                          variant="outline"
                          size="sm"
                          icon={ExternalLink}
                          onClick={() => navigate(`/products/${notif.productId}`)}
                        >
                          View Product
                        </Button>
                      )}
                      {!notif.isRead && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Check}
                          onClick={(e) => handleMarkAsRead(notif.id, e)}
                        >
                          Mark as Read
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Trash2}
                        style={{ color: 'var(--text-muted)' }}
                        onClick={(e) => handleDelete(notif.id, e)}
                      />
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </PageContainer>
  );
}
