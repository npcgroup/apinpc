import { FundingRate } from '../types/funding';
import { Layout } from 'plotly.js';

interface PlotlyData {
  x: (number | string)[];
  y: (number | string)[];
  type: 'scatter' | 'violin' | 'heatmap';
  mode?: string;
  name?: string;
  text?: string[];
  marker?: {
    size?: number;
    color?: number[] | string;
    colorscale?: string;
    showscale?: boolean;
    colorbar?: {
      title: string;
    };
  };
  line?: {
    color: string;
    dash?: string;
  };
  showlegend?: boolean;
  hovertemplate?: string;
}

export function createOpportunityScatter(rates: FundingRate[]) {
  const data: PlotlyData[] = [{
    x: rates.map(r => r.funding_rate),
    y: rates.map(r => r.predicted_rate),
    type: 'scatter',
    mode: 'markers',
    text: rates.map(r => r.symbol),
    marker: {
      size: 10,
      color: rates.map(r => r.opportunity_score),
      colorscale: 'RdYlGn',
      showscale: true,
      colorbar: {
        title: 'Opportunity Score'
      }
    },
    hovertemplate:
      '<b>%{text}</b><br>' +
      'Current Rate: %{x:.4f}%<br>' +
      'Predicted Rate: %{y:.4f}%<br>' +
      'Score: %{marker.color:.2f}<br>' +
      '<extra></extra>'
  }];

  const layout: Partial<Layout> = {
    title: 'Current vs Predicted Funding Rates',
    xaxis: { title: 'Current Funding Rate (%)' },
    yaxis: { title: 'Predicted Funding Rate (%)' },
    template: 'plotly_dark',
    showlegend: false
  };

  return { data, layout };
}

export function createExchangeComparison(rates: FundingRate[]) {
  const binanceRates = rates.filter(r => r.exchange === 'Binance');
  const hlRates = rates.filter(r => r.exchange === 'Hyperliquid');

  const data: PlotlyData[] = [
    {
      x: ['Hyperliquid'],
      y: hlRates.map(r => r.funding_rate),
      type: 'violin',
      name: 'Hyperliquid',
      line: {
        color: 'rgba(0,128,255,0.7)'
      },
      showlegend: true
    },
    {
      x: ['Binance'],
      y: binanceRates.map(r => r.funding_rate),
      type: 'violin',
      name: 'Binance',
      line: {
        color: 'rgba(240,128,0,0.7)'
      },
      showlegend: true
    }
  ];

  const layout: Partial<Layout> = {
    title: 'Funding Rate Distribution by Exchange',
    yaxis: { title: 'Funding Rate (%)' },
    template: 'plotly_dark',
    violinmode: 'group',
    showlegend: true
  };

  return { data, layout };
}

export function createFundingHeatmap(rates: FundingRate[]) {
  // Group rates by exchange and symbol
  const exchanges = ['Binance', 'Hyperliquid'];
  const symbols = [...new Set(rates.map(r => r.symbol))].sort();
  
  const heatmapData = symbols.map(symbol => {
    return exchanges.map(exchange => {
      const rate = rates.find(r => r.symbol === symbol && r.exchange === exchange);
      return rate ? rate.funding_rate : null;
    });
  });

  const data: PlotlyData[] = [{
    type: 'heatmap',
    x: exchanges,
    y: symbols,
    z: heatmapData as number[][],
    colorscale: 'RdBu',
    hovertemplate:
      '<b>%{y}</b><br>' +
      '%{x}<br>' +
      'Rate: %{z:.4f}%<br>' +
      '<extra></extra>'
  }];

  const layout: Partial<Layout> = {
    title: 'Funding Rate Heatmap',
    template: 'plotly_dark',
    xaxis: { title: 'Exchange' },
    yaxis: { title: 'Symbol' }
  };

  return { data, layout };
} 