import { DuneClient } from './duneClient';
import { FlipsideClient } from './flipsideClient';
import { NFT_QUERIES, formatNFTSalesResponse } from './sqlQueries';

interface QueryContext {
  metrics: string[];
  timeRange: string;
  protocols: string[];
  aggregation: string;
  chain?: string;
  question: string;
}

interface QueryResult {
  data: any;
  error?: string;
  metadata?: {
    type: string;
    timestamp: string;
  };
}

export async function handleNaturalLanguageQuery(
  service: 'dune' | 'flipside' | 'defillama',
  question: string,
  options: {
    chain?: string;
    dataset?: string;
    apiKey: string;
  }
): Promise<QueryResult> {
  try {
    // Validate required API key for services that need it
    if ((service === 'dune' || service === 'flipside') && !options.apiKey) {
      throw new Error(`${service} API key is required`);
    }

    const queryContext = await analyzeQuestion(question);
    
    switch(service) {
      case 'dune': {
        const duneClient = new DuneClient(options.apiKey);
        const duneSQL = await convertToSQL(queryContext, 'dune');
        const result = await duneClient.executeQuery(duneSQL);
        
        // Format NFT sales data if it's an NFT query
        if (queryContext.question.toLowerCase().includes('nft')) {
          return {
            data: formatNFTSalesResponse(result.data),
            metadata: {
              type: 'nft_sales',
              timestamp: new Date().toISOString()
            }
          };
        }
        
        return result;
      }
      
      case 'flipside': {
        const flipsideClient = new FlipsideClient(options.apiKey);
        const flipsideSQL = await convertToSQL(queryContext, 'flipside');
        return await flipsideClient.executeQuery(flipsideSQL);
      }
      
      case 'defillama':
        return await fetchDefiLlamaData(queryContext);
        
      default:
        throw new Error('Unsupported service');
    }
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

async function analyzeQuestion(question: string): Promise<QueryContext> {
  // Basic NLP analysis
  const metrics = extractMetrics(question.toLowerCase());
  const timeRange = extractTimeRange(question.toLowerCase());
  const protocols = extractProtocols(question.toLowerCase());
  
  return {
    metrics,
    timeRange,
    protocols,
    aggregation: determineAggregation(question),
    question
  };
}

function extractMetrics(question: string): string[] {
  const metricKeywords = {
    'tvl': ['tvl', 'total value locked', 'locked value'],
    'volume': ['volume', 'trading volume', 'traded'],
    'users': ['users', 'active users', 'unique users'],
    'fees': ['fees', 'revenue', 'earnings']
  };

  return Object.entries(metricKeywords)
    .filter(([_, keywords]) => keywords.some(k => question.includes(k)))
    .map(([metric]) => metric);
}

function extractTimeRange(question: string): string {
  const timeKeywords = {
    '1d': ['today', 'last 24 hours', '24h'],
    '7d': ['last week', '7 days', 'weekly'],
    '30d': ['last month', '30 days', 'monthly'],
    'ytd': ['this year', 'year to date', 'ytd']
  };

  for (const [range, keywords] of Object.entries(timeKeywords)) {
    if (keywords.some(k => question.includes(k))) {
      return range;
    }
  }
  return '7d'; // Default to 7 days
}

function extractProtocols(question: string): string[] {
  const protocolKeywords = [
    'uniswap', 'aave', 'curve', 'compound', 'maker',
    // Add more protocols
  ];

  return protocolKeywords.filter(p => question.includes(p.toLowerCase()));
}

function determineAggregation(question: string): string {
  if (question.includes('average') || question.includes('avg')) return 'avg';
  if (question.includes('total') || question.includes('sum')) return 'sum';
  if (question.includes('maximum') || question.includes('max')) return 'max';
  if (question.includes('minimum') || question.includes('min')) return 'min';
  return 'none';
}

async function convertToSQL(context: QueryContext, dialect: 'dune' | 'flipside'): Promise<string> {
  const { question } = context;
  
  // Check if it's an NFT query
  if (question.toLowerCase().includes('nft') || question.toLowerCase().includes('sales')) {
    return generateNFTQuery(context.timeRange);
  }

  // Template SQL based on context
  const { metrics, timeRange, protocols, aggregation } = context;
  
  const timeRangeSQL = {
    '1d': 'block_timestamp >= NOW() - INTERVAL \'1 day\'',
    '7d': 'block_timestamp >= NOW() - INTERVAL \'7 days\'',
    '30d': 'block_timestamp >= NOW() - INTERVAL \'30 days\'',
    'ytd': 'block_timestamp >= DATE_TRUNC(\'year\', NOW())'
  }[timeRange];

  // Build SQL based on metrics and context
  return `
    SELECT 
      DATE_TRUNC('day', block_timestamp) as date,
      ${metrics.map(m => `SUM(${m}) as ${m}`).join(',\n')}
    FROM ${dialect === 'dune' ? 'dune.eth' : 'ethereum.core'}.fact_transactions
    WHERE ${timeRangeSQL}
    ${protocols.length ? `AND protocol IN (${protocols.map(p => `'${p}'`).join(',')})` : ''}
    GROUP BY 1
    ORDER BY 1 DESC
  `;
}

async function fetchDefiLlamaData(context: QueryContext): Promise<QueryResult> {
  const baseUrl = 'https://api.llama.fi';
  const { protocols, metrics, timeRange } = context;
  
  // Construct API URL based on context
  const endpoint = protocols.length === 1 
    ? `/protocol/${protocols[0]}`
    : '/protocols';

  try {
    const response = await fetch(`${baseUrl}${endpoint}`);
    const data = await response.json();
    return { data };
  } catch (error) {
    return {
      data: null,
      error: 'Failed to fetch data from DefiLlama'
    };
  }
}

// Update the generateNFTQuery function
async function generateNFTQuery(timeRange: string): Promise<string> {
  return NFT_QUERIES.topSales;
} 