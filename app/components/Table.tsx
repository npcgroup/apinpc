import React from 'react'

interface TableProps {
  data: Array<{ key: string; value: string }>
}

export default function Table({ data }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-800">
            <th className="p-2 text-left">Key</th>
            <th className="p-2 text-left">Value</th>
          </tr>
        </thead>
        <tbody>
          {data.map(({ key, value }, i) => (
            <tr key={key} className={i % 2 ? 'bg-gray-800/50' : ''}>
              <td className="p-2 font-mono text-sm">{key}</td>
              <td className="p-2 font-mono text-sm">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
} 