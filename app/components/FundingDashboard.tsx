import React, { useEffect, useState, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { FundingRate, FundingStats, VisualizationData } from '../types/funding';
import { FundingService } from '../services/fundingService';
import { FundingMetrics } from './funding/FundingMetrics';
import { TopOpportunities } from './funding/TopOpportunities';
import { MarketAnalysis } from './funding/MarketAnalysis';
import { DetailedView } from './funding/DetailedView';
import { 
  createOpportunityScatter, 
  createExchangeComparison,
  createFundingHeatmap 
} from '../utils/visualizations';
import { ErrorBoundary } from 'react-error-boundary';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export const FundingDashboard: React.FC = () => {
  const [fundingData, setFundingData] = useState<{
    rates: FundingRate[];
    directional: any[];
    crossExchange: any[];
    detailed: any[];
  } | null>(null);
  const [stats, setStats] = useState<FundingStats | null>(null);
  const [vizData, setVizData] = useState<VisualizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fundingService = useMemo(() => new FundingService(), []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [ratesData, latestStats] = await Promise.all([
        fundingService.getPredictedRates(),
        fundingService.getLatestStats()
      ]);

      if (!ratesData.rates.length) {
        throw new Error('No funding rate data available');
      }

      const calculatedStats = latestStats || calculateStats(ratesData.rates);
      const visualizations = createVisualizations(ratesData.rates);

      setFundingData(ratesData);
      setStats(calculatedStats);
      setVizData(visualizations);

      await fundingService.pushToSupabase(
        ratesData.rates, 
        calculatedStats,
        visualizations
      );
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, []);

  const createVisualizations = (rates: FundingRate[]) => {
    return {
      opportunity_scatter: createOpportunityScatter(rates),
      exchange_comparison: createExchangeComparison(rates),
      funding_heatmap: createFundingHeatmap(rates),
      top_opportunities: rates
    };
  };

  const calculateStats = (rates: FundingRate[]): FundingStats => {
    const binanceRates = rates.filter(r => r.exchange === 'Binance');
    const hlRates = rates.filter(r => r.exchange === 'Hyperliquid');
    
    const avgRate = rates.reduce((sum, r) => sum + r.funding_rate, 0) / rates.length;
    
    return {
      total_markets: rates.length,
      binance_markets: binanceRates.length,
      hl_markets: hlRates.length,
      hourly_rate: avgRate,
      eight_hour_rate: avgRate * 8,
      daily_rate: avgRate * 24,
      timestamp: new Date()
    };
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Funding Rate Dashboard</h1>
      
      <FundingMetrics stats={stats} />

      {!loading && !error && stats && vizData && fundingData && (
        <div className="grid grid-cols-1 gap-4 mt-4">
          <TopOpportunities 
            directional={fundingData.directional}
            crossExchange={fundingData.crossExchange}
          />
          <MarketAnalysis vizData={vizData} />
          <DetailedView data={fundingData.detailed} />
        </div>
      )}

      {loading && (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 text-red-800 p-4 rounded-lg mt-4">
          <h3 className="font-semibold">Error loading data</h3>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}; 