import { readFileSync } from 'fs';
import { join } from 'path';
import matter from 'gray-matter';
import { marked } from 'marked';
import { DocSection } from './docHelpers';

interface DocMetadata {
  title?: string;
  description?: string;
  [key: string]: any;
}

interface ParsedDoc {
  metadata: DocMetadata;
  content: string;
}

export async function loadDocumentation(path: string): Promise<ParsedDoc> {
  const fullPath = join(process.cwd(), path);
  const fileContents = readFileSync(fullPath, 'utf8');
  const { data, content } = matter(fileContents);
  
  const parsedContent = await marked(content);
  return {
    metadata: data,
    content: parsedContent
  };
}

export async function processAllDocs() {
  try {
    const docs = {
      dune: await loadDocumentation('dune-docs/README.md'),
      footprint: await loadDocumentation('api-docs/footprint/README.md'),
      subgraphs: await loadDocumentation('subgraphs/README.md'),
    };
    return docs;
  } catch (error) {
    console.error('Error processing documentation:', error);
    return {
      dune: { metadata: {}, content: '' },
      footprint: { metadata: {}, content: '' },
      subgraphs: { metadata: {}, content: '' }
    };
  }
} 