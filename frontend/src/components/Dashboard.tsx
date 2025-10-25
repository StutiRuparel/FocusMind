import React from 'react';
import './Dashboard.css';
import AttentionScore from './AttentionScore';

interface DashboardProps {
  attentionScore: number;
  onDecreaseAttention: () => void;
  onGetNudgeQuote: () => void;
  loading: boolean;
}

const Dashboard: React.FC<DashboardProps> = ({ attentionScore, onDecreaseAttention, onGetNudgeQuote, loading }) => {
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
            >
              {loading ? 'Loading...' : 'Decrease Attention (-15)'}
            </button>
            <button 
              className="nudge-button"
              onClick={onGetNudgeQuote}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Get Nudge Quote 💪'}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
};

export default Dashboard;
