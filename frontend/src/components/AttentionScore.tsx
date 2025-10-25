import React from 'react';
import './AttentionScore.css';

interface AttentionScoreProps {
  score: number;
}

const AttentionScore: React.FC<AttentionScoreProps> = ({ score }) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10b981'; // Green
    if (score >= 60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    return 'Needs Focus';
  };

  // Calculate the circumference of the circle
  const radius = 50;
  const circumference = 2 * Math.PI * radius; // ≈ 314.159
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="attention-score">
      <div className="score-circle">
        <svg className="score-svg" viewBox="0 0 120 120">
          {/* Background circle */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke={getScoreColor(score)}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            className="progress-circle"
          />
        </svg>
        <div className="score-content">
          <div className="score-number" style={{ color: getScoreColor(score) }}>
            {score}
          </div>
          <div className="score-label">
            {getScoreLabel(score)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttentionScore;
