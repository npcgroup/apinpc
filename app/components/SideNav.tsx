'use client'

import React from 'react'

interface NavItem {
  id: string
  label: string
}

interface NavSection {
  title: string
  items: NavItem[]
}

interface SideNavProps {
  sections: NavSection[]
  activeSection: string
  onSectionChange: (id: string) => void
}

export const SideNav: React.FC<SideNavProps> = ({
  sections,
  activeSection,
  onSectionChange,
}) => {
  return (
    <nav className="w-64 bg-gray-900 p-4">
      {sections.map((section) => (
        <div key={section.title} className="mb-6">
          <h3 className="text-gray-400 text-sm font-semibold mb-2">
            {section.title}
          </h3>
          <ul>
            {section.items.map((item) => (
              <li key={item.id}>
                <button
                  className={`w-full text-left px-3 py-2 rounded ${
                    activeSection === item.id
                      ? 'bg-purple-500/20 text-purple-400'
                      : 'text-gray-400 hover:bg-gray-800'
                  }`}
                  onClick={() => onSectionChange(item.id)}
                >
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  )
} 