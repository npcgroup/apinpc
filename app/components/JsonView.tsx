import React from 'react'

interface JsonViewProps {
  data: any
}

export default function JsonView({ data }: JsonViewProps) {
  return (
    <pre className="p-4 bg-gray-800 rounded overflow-x-auto">
      <code>{JSON.stringify(data, null, 2)}</code>
    </pre>
  )
} 