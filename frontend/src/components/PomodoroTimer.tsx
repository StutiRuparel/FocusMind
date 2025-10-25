import React, { useState, useEffect, useCallback } from 'react';
import './PomodoroTimer.css';

interface PomodoroTimerProps {
  onBreakTime: () => void;  // Callback when timer reaches 0
}

const PomodoroTimer: React.FC<PomodoroTimerProps> = ({ onBreakTime }) => {
  const [timeLeft, setTimeLeft] = useState(25 * 60); // 25 minutes in seconds
  const [isRunning, setIsRunning] = useState(false);
  const [isBreak, setIsBreak] = useState(false);
  const [sessionCount, setSessionCount] = useState(0);

  // Pomodoro settings
  const WORK_TIME = 25 * 60; // 25 minutes
  const SHORT_BREAK = 5 * 60; // 5 minutes
  const LONG_BREAK = 15 * 60; // 15 minutes

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle timer completion
  const handleTimerComplete = useCallback(() => {
    if (!isBreak) {
      // Work session completed - time for a break!
      setSessionCount(prev => prev + 1);
      setIsBreak(true);
      
      // Determine break length (long break every 4 sessions)
      const isLongBreak = (sessionCount + 1) % 4 === 0;
      setTimeLeft(isLongBreak ? LONG_BREAK : SHORT_BREAK);
      
      // Trigger break nudge
      onBreakTime();
      
      console.log(`🍅 Pomodoro #${sessionCount + 1} complete! ${isLongBreak ? 'Long' : 'Short'} break time!`);
    } else {
      // Break completed - back to work!
      setIsBreak(false);
      setTimeLeft(WORK_TIME);
      setIsRunning(false); // Don't auto-start next work session
      
      console.log('⏰ Break time over! Ready for next work session.');
    }
  }, [isBreak, sessionCount, onBreakTime, WORK_TIME, SHORT_BREAK, LONG_BREAK]);

  // Timer countdown effect
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            setIsRunning(false);
            handleTimerComplete();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, timeLeft, handleTimerComplete]);

  const startTimer = () => setIsRunning(true);
  const pauseTimer = () => setIsRunning(false);
  
  const resetTimer = () => {
    setIsRunning(false);
    setTimeLeft(isBreak ? (sessionCount % 4 === 0 ? LONG_BREAK : SHORT_BREAK) : WORK_TIME);
  };

  const skipTimer = () => {
    setIsRunning(false);
    handleTimerComplete();
  };

  // Calculate progress percentage
  const totalTime = isBreak ? (sessionCount % 4 === 0 ? LONG_BREAK : SHORT_BREAK) : WORK_TIME;
  const progressPercentage = ((totalTime - timeLeft) / totalTime) * 100;

  return (
    <div className="pomodoro-timer">
      <div className="timer-header">
        <h2 className="timer-title">
          🍅 Pomodoro Timer
        </h2>
        <div className="session-info">
          <span className="session-count">Session #{sessionCount + (isBreak ? 0 : 1)}</span>
          <span className={`timer-mode ${isBreak ? 'break-mode' : 'work-mode'}`}>
            {isBreak 
              ? `${sessionCount % 4 === 0 ? 'Long' : 'Short'} Break` 
              : 'Focus Time'
            }
          </span>
        </div>
      </div>

      <div className="timer-display">
        <div className="timer-circle">
          <svg className="progress-ring" width="200" height="200">
            <circle
              className="progress-ring-bg"
              stroke="#e5e7eb"
              strokeWidth="8"
              fill="transparent"
              r="92"
              cx="100"
              cy="100"
            />
            <circle
              className={`progress-ring-progress ${isBreak ? 'break-progress' : 'work-progress'}`}
              stroke={isBreak ? "#10b981" : "#ef4444"}
              strokeWidth="8"
              strokeLinecap="round"
              fill="transparent"
              r="92"
              cx="100"
              cy="100"
              style={{
                strokeDasharray: `${2 * Math.PI * 92}`,
                strokeDashoffset: `${2 * Math.PI * 92 * (1 - progressPercentage / 100)}`,
                transition: 'stroke-dashoffset 1s linear'
              }}
            />
          </svg>
          <div className="timer-time">
            {formatTime(timeLeft)}
          </div>
        </div>
      </div>

      <div className="timer-controls">
        {!isRunning ? (
          <button 
            className="timer-btn start-btn"
            onClick={startTimer}
          >
            ▶️ Start
          </button>
        ) : (
          <button 
            className="timer-btn pause-btn"
            onClick={pauseTimer}
          >
            ⏸️ Pause
          </button>
        )}
        
        <button 
          className="timer-btn reset-btn"
          onClick={resetTimer}
        >
          🔄 Reset
        </button>
        
        <button 
          className="timer-btn skip-btn"
          onClick={skipTimer}
          title={isBreak ? "Skip break & start work" : "Skip to break"}
        >
          ⏭️ Skip
        </button>
      </div>

      <div className="timer-stats">
        <div className="stat">
          <span className="stat-label">Completed Sessions:</span>
          <span className="stat-value">{sessionCount}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Next Break:</span>
          <span className="stat-value">
            {sessionCount % 4 === 3 ? 'Long (15min)' : 'Short (5min)'}
          </span>
        </div>
      </div>

      {timeLeft === 0 && (
        <div className={`timer-notification ${isBreak ? 'break-complete' : 'work-complete'}`}>
          {isBreak 
            ? '⏰ Break time over! Ready to focus?' 
            : '🎉 Great work! Time for a break!'
          }
        </div>
      )}
    </div>
  );
};

export default PomodoroTimer;