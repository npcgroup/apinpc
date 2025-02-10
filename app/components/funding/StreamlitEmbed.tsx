'use client'

import { useEffect, useState } from 'react'
import { Card } from '../ui/card'
import { useToast } from '../ui/use-toast'

export function StreamlitEmbed() {
  const [loading, setLoading] = useState(true)
  const [streamlitUrl, setStreamlitUrl] = useState('')
  const { toast } = useToast()

  useEffect(() => {
    async function startStreamlit() {
      try {
        const res = await fetch('/api/funding')
        const data = await res.json()
        
        if (!res.ok) throw new Error(data.error)
        
        setStreamlitUrl(data.url)
        setLoading(false)
      } catch (error) {
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to load Streamlit app',
          variant: 'destructive'
        })
        setLoading(false)
      }
    }

    startStreamlit()
  }, [toast])

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500" />
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-0 overflow-hidden">
      <iframe
        src={streamlitUrl}
        width="100%"
        height="800px"
        frameBorder="0"
        title="Funding Dashboard"
        className="w-full"
      />
    </Card>
  )
} 