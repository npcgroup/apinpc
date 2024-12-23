'use client'

import React, { useState } from 'react'
import { Terminal, Download } from 'lucide-react'
import Table from './Table'
import JsonView from './JsonView'
import { convertToCSV } from '@/lib/formatters'

export default function ApiTerminal() {
  const [endpoint, setEndpoint] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<any>(null)
  const [viewMode, setViewMode] = useState<'table' | 'json'>('table')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      const res = await fetch('/api/proxy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ endpoint }),
      })

      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.error || 'Request failed')
      }

      setResponse(data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadCSV = () => {
    if (!response) return
    
    const csv = convertToCSV(response)
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'api-response.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <div className="flex items-center gap-2 mb-4">
        <Terminal className="w-5 h-5" />
        <h2 className="text-lg font-semibold">API Terminal</h2>
      </div>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            type="url"
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            placeholder="Enter API endpoint URL"
            className="flex-1 p-2 bg-gray-800 border border-gray-700 rounded"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-purple-500 rounded hover:bg-purple-600 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 mb-4 bg-red-500/20 border border-red-500/50 rounded">
          {error}
        </div>
      )}

      {response && (
        <div>
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1 rounded ${
                viewMode === 'table' ? 'bg-purple-500' : 'bg-gray-800'
              }`}
            >
              Table
            </button>
            <button
              onClick={() => setViewMode('json')}
              className={`px-3 py-1 rounded ${
                viewMode === 'json' ? 'bg-purple-500' : 'bg-gray-800'
              }`}
            >
              JSON
            </button>
            <button
              onClick={handleDownloadCSV}
              className="px-3 py-1 rounded bg-gray-800 hover:bg-gray-700 ml-auto flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Download CSV
            </button>
          </div>

          {viewMode === 'table' ? (
            <Table data={response} />
          ) : (
            <JsonView data={response} />
          )}
        </div>
      )}
    </div>
  )
} 