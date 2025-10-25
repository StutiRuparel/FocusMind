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
  source: string;
}

function App() {
  const [motivationData, setMotivationData] = useState<MotivationData | null>(null);
  const [loading, setLoading] = useState(false);

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

  const getNudgeQuote = async () => {
    setLoading(true);
    try {
      const response = await axios.post<NudgeResponse>('http://localhost:8000/get-nudge-quote');
      if (response.data.success && motivationData) {
        // Update the message with the new nudge quote
        setMotivationData({
          ...motivationData,
          message: response.data.message
        });
        console.log('💪 Got new David Goggins quote from nudge.py!');
      }
    } catch (error) {
      console.error('Error getting nudge quote:', error);
    } finally {
      setLoading(false);
    }
  };

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
        onGetNudgeQuote={getNudgeQuote}
        loading={loading}
      />
    </div>
  );
}

export default App;