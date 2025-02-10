'use client'

import React from 'react';
import { FundingStats } from '../../types/funding';
import { Card } from '../ui/card';

interface Props {
  stats: FundingStats | null;
}

export const FundingMetrics: React.FC<Props> = ({ stats }) => {
  if (!stats) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-gray-100 rounded-lg shadow p-4 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mt-2"></div>
          </div>
        ))}
      </div>
    );
  }

  const metrics = [
    {
      title: 'Total Markets',
      value: stats.total_markets,
      subtext: `${stats.binance_markets} Binance / ${stats.hl_markets} HL`
    },
    {
      title: '1H Rate',
      value: `${stats.hourly_rate.toFixed(4)}%`,
      subtext: `${(stats.hourly_rate * 365 * 24).toFixed(1)}% APR`
    },
    {
      title: '8H Rate',
      value: `${stats.eight_hour_rate.toFixed(4)}%`,
      subtext: `${(stats.eight_hour_rate * 365 / 8).toFixed(1)}% APR`
    },
    {
      title: '24H Rate',
      value: `${stats.daily_rate.toFixed(4)}%`,
      subtext: `${(stats.daily_rate * 365 / 24).toFixed(1)}% APR`
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <Card key={index} className="p-4 hover:shadow-lg transition-shadow">
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-700">{metric.title}</h3>
            <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
            <p className="text-sm text-gray-500">{metric.subtext}</p>
          </div>
        </Card>
      ))}
    </div>
  );
}; 