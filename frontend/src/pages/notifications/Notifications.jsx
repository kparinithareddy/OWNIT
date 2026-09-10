import React, { useState } from 'react';
import {
  Bell,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ShieldAlert,
  Trash2,
  Check
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import { mockNotifications } from '../../data/mockData';
import './Notifications.css';

export default function Notifications() {
  const [notifications, setNotifications] = useState(mockNotifications);

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
  };

  return (
    <PageContainer
      title="Notifications & Alerts"
      subtitle="Critical warranty countdowns, return expiration reminders, and maintenance prompts."
      actions={
        <Button
          variant="outline"
          icon={Check}
          onClick={markAllAsRead}
        >
          Mark All as Read
        </Button>
      }
    >
      <div className="notifications-container">
        {notifications.map((notif) => (
          <Card
            key={notif.id}
            className={`notif-card ${notif.unread ? 'notif-unread' : ''}`}
            padding="md"
          >
            <div className="notif-row">
              <div className={`notif-icon-box notif-icon-${notif.type}`}>
                {notif.type === 'warning' && <AlertTriangle size={20} />}
                {notif.type === 'info' && <Clock size={20} />}
                {notif.type === 'success' && <CheckCircle2 size={20} />}
              </div>

              <div className="notif-content">
                <div className="notif-header">
                  <h4 className="notif-title">{notif.title}</h4>
                  <span className="notif-time">{notif.date}</span>
                </div>
                <p className="notif-message">{notif.message}</p>
              </div>

              {notif.unread && (
                <div className="notif-unread-dot" title="Unread notification" />
              )}
            </div>
          </Card>
        ))}
      </div>
    </PageContainer>
  );
}
