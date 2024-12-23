'use client'

import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface CodeBlockProps {
  title?: string
  language: string
  code: string
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ title, language, code }) => {
  return (
    <div className="my-4">
      {title && (
        <div className="text-sm font-mono bg-gray-800 px-4 py-2 rounded-t">
          {title}
        </div>
      )}
      <SyntaxHighlighter
        language={language}
        style={atomDark}
        className="rounded-b"
      >
        {code.trim()}
      </SyntaxHighlighter>
    </div>
  )
} 