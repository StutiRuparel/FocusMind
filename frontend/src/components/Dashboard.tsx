import React from 'react';
import './Dashboard.css';
import AttentionScore from './AttentionScore';

interface DashboardProps {
  attentionScore: number;
  onDecreaseAttention: () => void;
  onGetVoiceNudge: () => void;
  onGetNotificationNudge: () => void;
  loading: boolean;
  nudgeExecuted: boolean;
  notificationSent: boolean;
  notificationPermission: NotificationPermission;
  onRequestNotificationPermission: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  attentionScore, 
  onDecreaseAttention, 
  onGetVoiceNudge, 
  onGetNotificationNudge, 
  loading, 
  nudgeExecuted, 
  notificationSent,
  notificationPermission,
  onRequestNotificationPermission
}) => {
  return (
    <main className="dashboard">
      <div className="dashboard-content">
        <div className="dashboard-grid">
          <div className="attention-section">
            <h2 className="section-title">Attention Score</h2>
            <AttentionScore score={attentionScore} />
          </div>
          
          <div className="actions-section">
            <button 
              className="decrease-button"
              onClick={onDecreaseAttention}
              disabled={loading}
              title="Attention will decrease and automatically trigger a voice nudge"
            >
              {loading ? 'Loading...' : 'Decrease Attention (-15) 🎤'}
            </button>
            
            <div className="nudge-buttons">
              <div className="auto-nudge-info" style={{
                marginBottom: '1rem',
                padding: '0.75rem',
                backgroundColor: '#f0f9ff',
                border: '1px solid #0ea5e9',
                borderRadius: '8px',
                fontSize: '0.9rem',
                color: '#0369a1'
              }}>
                🎤 <strong>Auto Voice Nudge:</strong> Every time your attention drops, David Goggins will automatically motivate you with a new message and read it aloud!
              </div>
              
              <button 
                className={`voice-nudge-button ${nudgeExecuted ? 'nudge-executed' : ''}`}
                onClick={onGetVoiceNudge}
                disabled={loading}
                title="Get a new voice nudge (happens automatically when attention drops)"
              >
                {loading ? 'Loading...' : 'Get New Voice Nudge 🎤'}
              </button>
              
              <button 
                className={`notification-nudge-button ${notificationSent ? 'notification-sent' : ''} ${notificationPermission === 'denied' ? 'permission-denied' : ''}`}
                onClick={notificationPermission === 'granted' ? onGetNotificationNudge : onRequestNotificationPermission}
                disabled={loading}
                title={
                  notificationPermission === 'granted' 
                    ? 'Send browser notification' 
                    : notificationPermission === 'denied'
                    ? 'Notifications blocked - check browser settings'
                    : 'Click to enable notifications'
                }
              >
                {loading ? 'Loading...' : 
                 notificationPermission === 'granted' ? 'Notification Nudge 🔔' :
                 notificationPermission === 'denied' ? 'Notifications Blocked 🚫' :
                 'Enable Notifications 🔔'}
              </button>
            </div>
            
            {/* Debug: Test notification button */}
            {notificationPermission === 'granted' && (
              <button 
                className="test-notification-button"
                onClick={() => {
                  console.log('🧪 Testing simple notification...');
                  if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification('Test Notification', {
                      body: 'This is a simple test notification',
                      icon: '/favicon.ico'
                    });
                  }
                }}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  marginTop: '0.5rem'
                }}
              >
                🧪 Test Simple Notification
              </button>
            )}
            
            {nudgeExecuted && (
              <div className="nudge-indicator voice-indicator">
                🎤 Voice Nudge Executed! Audio Playing...
              </div>
            )}
            
            {notificationSent && (
              <div className="nudge-indicator notification-indicator">
                🔔 Browser Notification Sent! Check your notifications.
              </div>
            )}
            
            {/* Debug: Permission status */}
            <div style={{
              marginTop: '1rem',
              padding: '0.5rem',
              backgroundColor: '#f3f4f6',
              borderRadius: '8px',
              fontSize: '0.8rem',
              color: '#374151'
            }}>
              🔐 Notification Permission: <strong>{notificationPermission}</strong>
              {notificationPermission === 'denied' && (
                <div style={{ marginTop: '0.25rem', color: '#ef4444' }}>
                  ⚠️ To enable: Click the lock icon in address bar → Allow notifications
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default Dashboard;
