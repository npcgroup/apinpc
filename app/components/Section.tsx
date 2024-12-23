'use client'

import React from 'react'

interface SectionProps {
  title: string
  children: React.ReactNode
}

export const Section: React.FC<SectionProps> = ({ title, children }) => {
  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold mb-4">{title}</h2>
      {children}
    </div>
  )
} 