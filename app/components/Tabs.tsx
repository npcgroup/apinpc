'use client'

import React from 'react'

interface TabsProps {
  activeTab: string
  children: React.ReactNode
}

export const Tabs: React.FC<TabsProps> = ({ activeTab, children }) => {
  return <div className="w-full">{children}</div>
}

export const TabList: React.FC<{children: React.ReactNode}> = ({ children }) => {
  return <div className="flex border-b border-gray-700">{children}</div>
}

interface TabProps {
  id: string
  active?: boolean
  onClick?: () => void
  children: React.ReactNode
}

export const Tab: React.FC<TabProps> = ({ id, active, onClick, children }) => {
  return (
    <button
      className={`px-4 py-2 ${active ? 'border-b-2 border-purple-500' : ''}`}
      onClick={onClick}
    >
      {children}
    </button>
  )
}

interface TabPanelProps {
  id: string
  children: React.ReactNode
  activeTab?: string
}

export const TabPanel: React.FC<TabPanelProps> = ({ id, children, activeTab }) => {
  if (activeTab !== id) {
    return null
  }
  
  return <div className="py-4">{children}</div>
} 