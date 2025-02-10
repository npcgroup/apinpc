'use client'

import React from 'react';
import dynamic from 'next/dynamic';
import { VisualizationData } from '../../types/funding';
import { PlotParams } from 'react-plotly.js';
import { ErrorBoundary } from '../ErrorBoundary';

// Type the Plot component
const Plot = dynamic<PlotParams>(() => import('react-plotly.js'), { ssr: false });

interface Props {
  vizData: VisualizationData;
}

export const MarketAnalysis: React.FC<Props> = ({ vizData }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-xl font-semibold mb-4">Market Analysis</h2>
      
      <div className="grid grid-cols-2 gap-4">
        {/* Exchange Comparison */}
        {vizData.exchange_comparison && (
          <div className="col-span-2">
            <ErrorBoundary>
              <Plot
                data={vizData.exchange_comparison.data}
                layout={{
                  ...vizData.exchange_comparison.layout,
                  height: 500,
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)',
                  margin: { t: 40, r: 40, b: 40, l: 40 }
                }}
                config={{ responsive: true }}
                useResizeHandler
                style={{ width: '100%', height: '100%' }}
              />
            </ErrorBoundary>
          </div>
        )}

        {/* Distribution Plot */}
        {vizData.funding_distribution && (
          <div>
            <ErrorBoundary>
              <Plot
                data={vizData.funding_distribution.data}
                layout={{
                  ...vizData.funding_distribution.layout,
                  height: 400,
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)',
                  margin: { t: 40, r: 40, b: 40, l: 40 }
                }}
                config={{ responsive: true }}
                useResizeHandler
                style={{ width: '100%', height: '100%' }}
              />
            </ErrorBoundary>
          </div>
        )}

        {/* Heatmap */}
        {vizData.funding_heatmap && (
          <div>
            <ErrorBoundary>
              <Plot
                data={vizData.funding_heatmap.data}
                layout={{
                  ...vizData.funding_heatmap.layout,
                  height: 400,
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)',
                  margin: { t: 40, r: 40, b: 40, l: 40 }
                }}
                config={{ responsive: true }}
                useResizeHandler
                style={{ width: '100%', height: '100%' }}
              />
            </ErrorBoundary>
          </div>
        )}
      </div>
    </div>
  );
}; 