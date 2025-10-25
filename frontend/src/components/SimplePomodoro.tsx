import React, { useState, useEffect } from 'react';

const SimplePomodoro: React.FC = () => {
  const [timeLeft, setTimeLeft] = useState(25 * 60); // 25 minutes
  const [isRunning, setIsRunning] = useState(false);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Timer countdown effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            setIsRunning(false);
            alert('🍅 Pomodoro Complete! Time for a break!');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, timeLeft]);

  const startTimer = () => setIsRunning(true);
  const pauseTimer = () => setIsRunning(false);
  const resetTimer = () => {
    setIsRunning(false);
    setTimeLeft(25 * 60);
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
      borderRadius: '16px',
      padding: '2rem',
      maxWidth: '400px',
      margin: '2rem auto',
      textAlign: 'center',
      boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)'
    }}>
      <h2 style={{ margin: '0 0 1rem 0', color: '#1f2937' }}>
        🍅 Pomodoro Timer
      </h2>
      
      <div style={{
        fontSize: '3rem',
        fontWeight: 'bold',
        color: '#1f2937',
        margin: '2rem 0',
        fontFamily: 'monospace'
      }}>
        {formatTime(timeLeft)}
      </div>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        {!isRunning ? (
          <button 
            onClick={startTimer}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            ▶️ Start
          </button>
        ) : (
          <button 
            onClick={pauseTimer}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            ⏸️ Pause
          </button>
        )}
        
        <button 
          onClick={resetTimer}
          style={{
            padding: '0.75rem 1.5rem',
            background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          🔄 Reset
        </button>
      </div>

      <div style={{ 
        marginTop: '1rem', 
        fontSize: '0.9rem', 
        color: '#6b7280' 
      }}>
        {isRunning ? '⏰ Timer is running...' : '⏸️ Timer is paused'}
      </div>
    </div>
  );
};

export default SimplePomodoro;