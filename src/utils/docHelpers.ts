import type { ApiEndpoint } from '../types/api';
import { readFileSync } from 'fs';
import { join } from 'path';

// Import documentation as raw strings
const duneEndpoints = readFileSync(join(process.cwd(), 'dune-docs/api-reference/executions/endpoint/README.md'), 'utf8');
const footprintDocs = readFileSync(join(process.cwd(), 'api-docs/footprint/README.md'), 'utf8');
const subgraphDocs = readFileSync(join(process.cwd(), 'subgraphs/README.md'), 'utf8');
const defiLlamaDocs = readFileSync(join(process.cwd(), 'api-docs/defillama/README.md'), 'utf8');

export interface DocSection {
  title: string;
  content: string;
  examples?: string[];
}

export function parseMarkdownDocs(content: string): DocSection[] {
  // Parse markdown content into structured sections
  const sections: DocSection[] = [];
  const lines = content.split('\n');
  let currentSection: DocSection | null = null;

  lines.forEach(line => {
    if (line.startsWith('#')) {
      if (currentSection) {
        sections.push(currentSection);
      }
      currentSection = {
        title: line.replace(/^#+\s+/, ''),
        content: '',
        examples: []
      };
    } else if (currentSection) {
      currentSection.content += line + '\n';
    }
  });

  if (currentSection) {
    sections.push(currentSection);
  }

  return sections;
}

export function formatEndpointDocs(endpoints: any[]): ApiEndpoint[] {
  return endpoints.map(endpoint => ({
    method: endpoint.method,
    path: endpoint.path,
    description: endpoint.description,
    parameters: endpoint.parameters,
    examples: endpoint.examples,
    authentication: endpoint.authentication,
    rateLimit: endpoint.rateLimit,
    category: endpoint.category,
    schema: endpoint.schema
  }));
}

// Export parsed documentation
export const documentation = {
  dune: parseMarkdownDocs(duneEndpoints),
  footprint: parseMarkdownDocs(footprintDocs),
  subgraph: parseMarkdownDocs(subgraphDocs),
  defiLlama: parseMarkdownDocs(defiLlamaDocs)
}; 