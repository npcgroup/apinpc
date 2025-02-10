'use client'

import React, { useState, useEffect } from 'react'
import { FundingMetrics } from '../components/funding/FundingMetrics'
import { FundingOpportunities } from '../components/funding/FundingOpportunities'
import { MarketAnalysis } from '../components/funding/MarketAnalysis'
import { DetailedView } from '../components/funding/DetailedView'
import { RefreshButton } from '../components/funding/RefreshButton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { useToast } from '../components/ui/use-toast'
import { Card } from '../components/ui/card'
import { ToastProvider } from '../components/ui/toast'
import { FundingRate, FundingStats, VisualizationData } from '../types/funding'

interface DashboardData {
  stats: FundingStats;
  opportunities: {
    directional: FundingRate[];
    crossExchange: any[];
  };
  analysis: VisualizationData;
  detailed: FundingRate[];
}

export default function FundingDashboard() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<DashboardData | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/funding')
      const json = await res.json()
      
      if (!res.ok) throw new Error(json.error)
      
      setData(json)
      setLastUpdate(new Date())
      toast({
        title: "Data refreshed",
        description: "Latest funding data has been loaded"
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to fetch data",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchData, 300000)
    return () => clearInterval(interval)
  }, [])

  return (
    <ToastProvider>
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">Funding Rate Dashboard</h1>
          <RefreshButton onClick={fetchData} loading={loading} lastUpdate={lastUpdate} />
        </div>

        {data && (
          <>
            <FundingMetrics stats={data.stats} />

            <Tabs defaultValue="opportunities" className="w-full">
              <TabsList className="w-full justify-start">
                <TabsTrigger value="opportunities">🎯 Top Opportunities</TabsTrigger>
                <TabsTrigger value="analysis">📊 Market Analysis</TabsTrigger>
                <TabsTrigger value="detailed">🔍 Detailed View</TabsTrigger>
              </TabsList>

              <TabsContent value="opportunities">
                <Card className="p-6">
                  <FundingOpportunities 
                    directional={data.opportunities.directional}
                    crossExchange={data.opportunities.crossExchange}
                  />
                </Card>
              </TabsContent>

              <TabsContent value="analysis">
                <Card className="p-6">
                  <MarketAnalysis vizData={data.analysis} />
                </Card>
              </TabsContent>

              <TabsContent value="detailed">
                <Card className="p-6">
                  <DetailedView data={data.detailed} />
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </ToastProvider>
  )
} 