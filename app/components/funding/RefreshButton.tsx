'use client'

import { Button } from '../ui/button'
import { Loader2 } from 'lucide-react'

interface RefreshButtonProps {
  onClick: () => void
  loading: boolean
  lastUpdate: Date | null
}

export function RefreshButton({ onClick, loading, lastUpdate }: RefreshButtonProps) {
  return (
    <div className="flex items-center gap-4">
      {lastUpdate && (
        <p className="text-sm text-gray-400">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </p>
      )}
      <Button 
        onClick={onClick}
        disabled={loading}
        variant="outline"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Refreshing...
          </>
        ) : (
          'Refresh Data'
        )}
      </Button>
    </div>
  )
} 