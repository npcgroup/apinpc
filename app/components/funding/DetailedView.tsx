'use client'

import React, { useState, useMemo } from 'react'
import { Card } from '../ui/card'
import { Input } from '../ui/input'
import { formatPercent, formatUSD } from '@/lib/formatters'
import { FundingRate } from '../../types/funding'

interface DetailedViewProps {
  data: FundingRate[]
}

export const DetailedView: React.FC<DetailedViewProps> = ({ data }) => {
  const [sortField, setSortField] = useState<keyof FundingRate>('opportunity_score')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [filter, setFilter] = useState('')

  const sortedData = useMemo(() => {
    let filtered = data
    
    if (filter) {
      filtered = data.filter(item => 
        item.symbol.toLowerCase().includes(filter.toLowerCase()) ||
        item.exchange.toLowerCase().includes(filter.toLowerCase())
      )
    }

    return [...filtered].sort((a, b) => {
      const aValue = a[sortField]
      const bValue = b[sortField]
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
      }
      
      return sortDirection === 'asc' 
        ? String(aValue).localeCompare(String(bValue))
        : String(bValue).localeCompare(String(aValue))
    })
  }, [data, sortField, sortDirection, filter])

  const handleSort = (field: keyof FundingRate) => {
    if (field === sortField) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-xl font-semibold mb-4">Detailed View</h2>
      
      <div className="mb-4">
        <input
          type="text"
          placeholder="Filter by symbol or exchange..."
          className="w-full px-4 py-2 border rounded"
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b">
              {['Symbol', 'Exchange', 'Funding Rate', 'Predicted Rate', 'Diff', 
                'Time to Funding', 'Direction', 'APR', 'Score', 'Price'].map(header => {
                const field = header.toLowerCase().replace(' ', '_') as keyof FundingRate
                return (
                  <th 
                    key={header}
                    className="px-4 py-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort(field)}
                  >
                    {header}
                    {sortField === field && (
                      <span className="ml-1">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {sortedData.map((item, idx) => (
              <tr key={`${item.symbol}-${item.exchange}`} 
                  className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                <td className="px-4 py-2">{item.symbol}</td>
                <td className="px-4 py-2">{item.exchange}</td>
                <td className="px-4 py-2">{item.funding_rate.toFixed(4)}%</td>
                <td className="px-4 py-2">{item.predicted_rate.toFixed(4)}%</td>
                <td className="px-4 py-2">{item.rate_diff.toFixed(4)}%</td>
                <td className="px-4 py-2">{item.time_to_funding}h</td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-1 rounded ${
                    item.direction === 'long' 
                      ? 'bg-green-100 text-green-800'
                      : item.direction === 'short'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {item.direction}
                  </span>
                </td>
                <td className="px-4 py-2">{item.annualized_rate.toFixed(2)}%</td>
                <td className="px-4 py-2">{item.opportunity_score.toFixed(2)}</td>
                <td className="px-4 py-2">${item.mark_price.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
} 