'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Book, Database, Code, Zap, Search, Terminal } from 'lucide-react';
import { API_EXAMPLES, DOCUMENTATION_SECTIONS, API_REFERENCE } from '../utils/docExamples';
import type { ApiEndpoint } from '../types/api';

interface SearchResult {
  title: string;
  content: string;
  type: 'endpoint' | 'example' | 'guide';
  source: string;
}

// Add content rendering components
function ContentSection({ content }: { content: string }) {
  return (
    <div className="prose prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: content }} />
  );
}

function EndpointCard({ endpoint }: { endpoint: ApiEndpoint }) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
      <div className="flex items-center gap-2 mb-4">
        <span className={`px-2 py-1 rounded text-xs font-medium
          ${endpoint.method === 'GET' ? 'bg-blue-500/20 text-blue-400' :
            endpoint.method === 'POST' ? 'bg-green-500/20 text-green-400' :
            endpoint.method === 'PUT' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-red-500/20 text-red-400'}`}>
          {endpoint.method}
        </span>
        <code className="text-gray-300">{endpoint.path}</code>
      </div>
      <p className="text-gray-400 mb-4">{endpoint.description}</p>
      
      {endpoint.parameters && endpoint.parameters.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Parameters</h4>
          <table className="min-w-full divide-y divide-gray-700">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-400">Name</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-400">Type</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-400">Required</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-400">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {endpoint.parameters.map(param => (
                <tr key={param.name}>
                  <td className="px-4 py-2 text-sm font-mono text-purple-400">{param.name}</td>
                  <td className="px-4 py-2 text-sm text-gray-300">{param.type}</td>
                  <td className="px-4 py-2 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      param.required ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {param.required ? 'Required' : 'Optional'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-400">{param.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {endpoint.examples && endpoint.examples.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-300 mb-2">Examples</h4>
          <div className="space-y-4">
            {endpoint.examples.map((example, index) => (
              <div key={index} className="bg-gray-900/50 rounded-lg p-4">
                <h5 className="text-sm font-medium text-gray-400 mb-2">{example.title}</h5>
                <pre className="overflow-x-auto p-4 bg-black/50 rounded-lg">
                  <code className="text-sm text-gray-300">{example.code}</code>
                </pre>
                {example.response && (
                  <div className="mt-2">
                    <h6 className="text-xs font-medium text-gray-500 mb-1">Response</h6>
                    <pre className="overflow-x-auto p-4 bg-black/50 rounded-lg">
                      <code className="text-sm text-gray-300">{example.response}</code>
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Add type definitions for the API reference and documentation sections
type Provider = 'defillama' | 'dune' | 'flipside' | 'graph' | 'all';
type Section = 'overview' | 'defi' | 'nft' | 'dex' | 'queries';

interface ApiReferenceData {
  baseUrl: string;
  description: string;
  authentication: string;
  rateLimits: string | { [key: string]: string };
  endpoints: ApiEndpoint[];
}

interface DocumentationSection {
  title: string;
  content: string;
}

// Update the MainContent component with proper types
function MainContent({ 
  activeSection, 
  selectedProvider 
}: { 
  activeSection: string; 
  selectedProvider: Provider;
}) {
  // Type guard to check if provider exists in API_REFERENCE
  const providerKey = selectedProvider === 'all' ? 'defillama' : selectedProvider;
  const docs = API_REFERENCE[providerKey as keyof typeof API_REFERENCE] as ApiReferenceData | undefined;
  
  // Type guard to check if section exists in DOCUMENTATION_SECTIONS
  const content = DOCUMENTATION_SECTIONS[activeSection as keyof typeof DOCUMENTATION_SECTIONS] as DocumentationSection | undefined;

  return (
    <div className="space-y-8">
      {content && <ContentSection content={content.content} />}
      
      {docs && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-200">{docs.description}</h2>
          
          {docs.authentication && (
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
              <h3 className="text-lg font-semibold text-gray-300 mb-2">Authentication</h3>
              <p className="text-gray-400">{docs.authentication}</p>
            </div>
          )}

          {docs.endpoints && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-300">Endpoints</h3>
              {docs.endpoints.map((endpoint: ApiEndpoint) => (
                <EndpointCard key={endpoint.path} endpoint={endpoint} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Update the main component state types
export default function ApiDocs() {
  const [activeSection, setActiveSection] = useState<Section>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<Provider>('all');

  // Navigation sections based on all our docs
  const sections = [
    { id: 'overview', label: 'Overview', icon: Book },
    { id: 'defi', label: 'DeFi Analytics', icon: Database },
    { id: 'nft', label: 'NFT Data', icon: Code },
    { id: 'dex', label: 'DEX Metrics', icon: Zap },
    { id: 'queries', label: 'SQL Queries', icon: Terminal }
  ];

  // Data providers from our documentation
  const providers = [
    { id: 'all', name: 'All Sources' },
    { id: 'dune', name: 'Dune Analytics' },
    { id: 'flipside', name: 'Flipside Crypto' },
    { id: 'defillama', name: 'DefiLlama' },
    { id: 'graph', name: 'The Graph' }
  ];

  // Update the state setters and handlers with proper types
  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value as Provider;
    setSelectedProvider(newProvider);
  };

  const handleSectionChange = (newSection: string) => {
    const validSection = newSection as Section;
    setActiveSection(validSection);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-black">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gray-900/50 border-b border-gray-700/50">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:py-24 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-red-500">
              Blockchain Data Documentation
            </h1>
            <p className="mt-4 text-xl text-gray-400">
              Comprehensive access to on-chain data across multiple protocols and chains
            </p>
          </div>
        </div>
        <div className="absolute inset-0 bg-gradient-to-r from-purple-800/20 via-pink-800/20 to-red-800/20 animate-gradient-x" />
      </div>

      {/* Search Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search documentation..."
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Search className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>
          <select
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500"
            value={selectedProvider}
            onChange={handleProviderChange}
          >
            {providers.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-12 gap-8">
          {/* Sidebar Navigation */}
          <div className="col-span-3">
            <nav className="space-y-1">
              {sections.map(section => (
                <button
                  key={section.id}
                  onClick={() => handleSectionChange(section.id)}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg ${
                    activeSection === section.id
                      ? 'bg-purple-500/20 text-purple-400'
                      : 'text-gray-400 hover:bg-gray-800'
                  }`}
                >
                  <section.icon className="mr-3 h-5 w-5" />
                  {section.label}
                </button>
              ))}
            </nav>

            {/* Quick Links */}
            <div className="mt-8">
              <h3 className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Quick Links
              </h3>
              <div className="mt-2 space-y-1">
                <a href="#examples" className="block px-3 py-2 text-sm text-gray-400 hover:bg-gray-800 rounded-lg">
                  Example Queries
                </a>
                <a href="#schemas" className="block px-3 py-2 text-sm text-gray-400 hover:bg-gray-800 rounded-lg">
                  Schema Reference
                </a>
                <a href="#authentication" className="block px-3 py-2 text-sm text-gray-400 hover:bg-gray-800 rounded-lg">
                  Authentication
                </a>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="col-span-9">
            <MainContent activeSection={activeSection} selectedProvider={selectedProvider} />
          </div>
        </div>
      </div>
    </div>
  );
} 