import React, { useEffect, useState } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import { FundingStrategyManager } from '../strategies/funding/FundingStrategyManager';
import { StrategySignal, MarketTrend } from '../strategies/funding/types';

interface FundingAnalyticsProps {
  supabaseUrl: string;
  supabaseKey: string;
}

export const FundingAnalytics: React.FC<FundingAnalyticsProps> = ({ supabaseUrl, supabaseKey }) => {
  const [sentiment, setSentiment] = useState<Map<string, StrategySignal>>(new Map());
  const [trends, setTrends] = useState<Map<string, MarketTrend>>(new Map());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const strategyManager = new FundingStrategyManager(supabaseUrl, supabaseKey);
    
    const fetchData = async () => {
      try {
        const [sentimentData, trendData] = await Promise.all([
          strategyManager.analyzeSentiment(),
          strategyManager.analyzeTrendDivergence()
        ]);
        
        setSentiment(sentimentData);
        setTrends(trendData);
      } catch (error) {
        console.error('Error fetching funding data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000); // Update every 5 minutes
    
    return () => clearInterval(interval);
  }, [supabaseUrl, supabaseKey]);

  if (loading) return <div>Loading funding analytics...</div>;

  return (
    <div className="funding-analytics">
      <div className="sentiment-analysis">
        <h2>Market Sentiment</h2>
        <div className="sentiment-grid">
          {Array.from(sentiment.entries()).map(([asset, signal]) => (
            <div key={asset} className={`sentiment-card ${signal.signal}`}>
              <h3>{asset}</h3>
              <p>Signal: {signal.signal}</p>
              <p>Strength: {(signal.strength * 100).toFixed(2)}%</p>
              <p>Funding Rate: {(signal.fundingRate * 100).toFixed(4)}%</p>
            </div>
          ))}
        </div>
      </div>

      <div className="trend-divergence">
        <h2>Trend Analysis</h2>
        <div className="trend-grid">
          {Array.from(trends.entries()).map(([asset, trend]) => (
            <div key={asset} className={`trend-card ${trend.divergence ? 'divergent' : 'convergent'}`}>
              <h3>{asset}</h3>
              <p>Price Trend: {trend.priceTrend}</p>
              <p>Funding Trend: {trend.fundingTrend}</p>
              <p>Confidence: {(trend.confidence * 100).toFixed(2)}%</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}; 