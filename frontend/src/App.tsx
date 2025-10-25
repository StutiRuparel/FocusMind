import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Dashboard from './components/Dashboard';
import Header from './components/Header';

interface MotivationData {
  message: string;
  attention_score: number;
}

interface AttentionResponse {
  attention_score: number;
  message: string;
}

interface NudgeResponse {
  success: boolean;
  message: string;
  audio_url?: string;
  audio_file?: string;
  source: string;
  nudge_type?: string;
  platform?: string;
}

function App() {
  const [motivationData, setMotivationData] = useState<MotivationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [nudgeExecuted, setNudgeExecuted] = useState(false);
  const [notificationSent, setNotificationSent] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');

  // Request notification permission on app load
  useEffect(() => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
      
      if (Notification.permission === 'default') {
        Notification.requestPermission().then((permission) => {
          setNotificationPermission(permission);
          console.log('🔔 Notification permission:', permission);
        });
      }
    } else {
      console.warn('🚫 This browser does not support notifications');
    }
  }, []);

  // Function to show browser notification
  const showBrowserNotification = (title: string, message: string, icon?: string) => {
    console.log('🔔 Attempting to show notification...');
    console.log('📋 Title:', title);
    console.log('📋 Message:', message);
    console.log('🌐 Notification support:', 'Notification' in window);
    console.log('🔐 Permission status:', Notification.permission);
    
    if (!('Notification' in window)) {
      console.error('🚫 Browser does not support notifications');
      alert('Your browser does not support notifications');
      return null;
    }

    if (Notification.permission === 'denied') {
      console.error('🚫 Notifications are blocked. Please enable them in browser settings.');
      alert('Notifications are blocked. Please enable them in your browser settings:\n\n1. Click the lock icon in the address bar\n2. Set Notifications to "Allow"');
      return null;
    }

    if (Notification.permission === 'default') {
      console.log('🔔 Requesting notification permission...');
      Notification.requestPermission().then((permission) => {
        console.log('🔐 Permission result:', permission);
        setNotificationPermission(permission);
        if (permission === 'granted') {
          // Retry showing notification after permission granted
          showBrowserNotification(title, message, icon);
        }
      });
      return null;
    }

    if (Notification.permission === 'granted') {
      console.log('✅ Permission granted, creating notification...');
      try {
        const notification = new Notification(title, {
          body: message,
          icon: icon || '/favicon.ico',
          badge: '/favicon.ico',
          tag: 'focusmind-nudge',
          requireInteraction: false, // Changed to false for better compatibility
          silent: false
        });

        console.log('✅ Notification created successfully!');

        // Auto-close after 8 seconds
        setTimeout(() => {
          notification.close();
          console.log('🔔 Notification auto-closed');
        }, 8000);

        // Handle notification events
        notification.onshow = () => {
          console.log('🔔 Notification is now visible');
        };

        notification.onclick = () => {
          console.log('🔔 Notification clicked');
          window.focus();
          notification.close();
        };

        notification.onerror = (error) => {
          console.error('🚫 Notification error:', error);
        };

        notification.onclose = () => {
          console.log('🔔 Notification closed');
        };

        return notification;
      } catch (error) {
        console.error('🚫 Error creating notification:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        alert('Error creating notification: ' + errorMessage);
        return null;
      }
    }

    console.warn('🚫 Unknown permission state:', Notification.permission);
    return null;
  };

  const fetchMotivation = async (reset: boolean = false) => {
    setLoading(true);
    try {
      const url = reset 
        ? 'http://localhost:8000/motivation?reset=true'
        : 'http://localhost:8000/motivation';
      const response = await axios.get<MotivationData>(url);
      setMotivationData(response.data);
    } catch (error) {
      console.error('Error fetching motivation:', error);
    } finally {
      setLoading(false);
    }
  };

  const decreaseAttention = async () => {
    setLoading(true);
    try {
      const response = await axios.post<AttentionResponse>('http://localhost:8000/decrease-attention');
      const newScore = response.data.attention_score;
      
      // Update the attention score in our state
      if (motivationData) {
        setMotivationData({
          ...motivationData,
          attention_score: newScore
        });
        
        // If attention score drops below 80, automatically get new motivation
        if (newScore < 80 && motivationData.attention_score >= 80) {
          console.log('🚨 Attention dropped below 80! Getting new motivation...');
          // Fetch new motivation after a short delay to show the score change first
          setTimeout(() => {
            fetchMotivation(false);
          }, 1000);
        }
      }
    } catch (error) {
      console.error('Error decreasing attention:', error);
    } finally {
      setLoading(false);
    }
  };

  const getVoiceNudge = async () => {
    setLoading(true);
    setNudgeExecuted(false); // Reset indicator
    
    try {
      console.log('🚀 Calling voice nudge...');
      const response = await axios.post<NudgeResponse>('http://localhost:8000/get-voice-nudge');
      
      if (response.data.success && motivationData) {
        // Set visual indicator that nudge script executed
        setNudgeExecuted(true);
        
        // Update the message with the new nudge quote
        setMotivationData({
          ...motivationData,
          message: response.data.message
        });
        
        console.log('💪 Got new David Goggins voice quote!');
        console.log('🎯 Voice nudge executed successfully!');
        
        // Play audio if available
        if (response.data.audio_url) {
          const audioUrl = `http://localhost:8000${response.data.audio_url}`;
          console.log('🔊 Playing voiceover:', audioUrl);
          
          const audio = new Audio(audioUrl);
          audio.volume = 0.8; // Set volume to 80%
          
          // Add event listeners for better user experience
          audio.onloadstart = () => console.log('🎵 Loading audio...');
          audio.oncanplay = () => console.log('🎵 Audio ready to play');
          audio.onplay = () => console.log('🎵 Audio started playing');
          audio.onended = () => {
            console.log('🎵 Audio finished playing');
            // Keep the visual indicator for 3 more seconds after audio ends
            setTimeout(() => setNudgeExecuted(false), 3000);
          };
          audio.onerror = (e) => console.error('🚫 Audio playback error:', e);
          
          // Play the audio
          try {
            await audio.play();
          } catch (playError) {
            console.error('Audio play failed (user interaction may be required):', playError);
            // Keep indicator visible even if audio fails
            setTimeout(() => setNudgeExecuted(false), 5000);
          }
        } else {
          // No audio, hide indicator after 3 seconds
          setTimeout(() => setNudgeExecuted(false), 3000);
        }
      }
    } catch (error) {
      console.error('Error getting voice nudge:', error);
      setNudgeExecuted(false);
    } finally {
      setLoading(false);
    }
  };

  const getNotificationNudge = async () => {
    setLoading(true);
    setNotificationSent(false); // Reset indicator
    
    try {
      console.log('🔔 Generating browser notification nudge...');
      
      // Generate motivational message using our backend
      const response = await axios.post<NudgeResponse>('http://localhost:8000/get-notification-nudge');
      
      if (response.data.success) {
        // Set visual indicator that notification was sent
        setNotificationSent(true);
        
        console.log('📢 Notification nudge generated successfully!');
        console.log('💪 Message:', response.data.message);
        
        // Show browser notification
        const cleanMessage = response.data.message.replace(/"/g, ''); // Remove quotes from message
        const notification = showBrowserNotification(
          '💪 FocusMind Nudge',
          cleanMessage,
          '/favicon.ico'
        );
        
        if (notification) {
          console.log('🔔 Browser notification shown successfully!');
        } else {
          console.warn('⚠️ Could not show browser notification - check permissions');
        }
        
        // Hide indicator after 4 seconds
        setTimeout(() => setNotificationSent(false), 4000);
      }
    } catch (error) {
      console.error('Error generating notification nudge:', error);
      
      // Fallback: Show a generic notification even if API fails
      const fallbackMessage = "Time to refocus! Get back to your studies and crush those goals! 💪";
      const notification = showBrowserNotification(
        '💪 FocusMind Nudge',
        fallbackMessage
      );
      
      if (notification) {
        setNotificationSent(true);
        setTimeout(() => setNotificationSent(false), 4000);
      } else {
        setNotificationSent(false);
      }
    } finally {
      setLoading(false);
    }
  };

  // Keep the old function name for backward compatibility
  const getNudgeQuote = getVoiceNudge;

  useEffect(() => {
    // Reset attention score to 100 on page load/refresh
    fetchMotivation(true);
  }, []);

  return (
    <div className="App">
      <Header 
        message={motivationData?.message || "Loading motivation..."} 
        loading={loading}
      />
      <Dashboard 
        attentionScore={motivationData?.attention_score || 0}
        onDecreaseAttention={decreaseAttention}
        onGetVoiceNudge={getVoiceNudge}
        onGetNotificationNudge={getNotificationNudge}
        loading={loading}
        nudgeExecuted={nudgeExecuted}
        notificationSent={notificationSent}
        notificationPermission={notificationPermission}
        onRequestNotificationPermission={() => {
          if ('Notification' in window) {
            Notification.requestPermission().then((permission) => {
              setNotificationPermission(permission);
            });
          }
        }}
      />
    </div>
  );
}

export default App;