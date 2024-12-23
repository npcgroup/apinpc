const path = require('path');
require('dotenv').config({ path: path.resolve(process.cwd(), '.env.local') });

// Add debug logging
console.log('Current directory:', process.cwd());
console.log('Env file path:', path.resolve(process.cwd(), '.env.local'));
console.log('Environment variables loaded:', {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL,
  // Don't log the actual key for security
  hasSupabaseKey: !!process.env.NEXT_PUBLIC_SUPABASE_KEY
});

const { DataIngestionService } = require('../services/dataIngestion');
const { supabase } = require('../lib/supabaseClient');
import { ErrorWithDetails } from '../types/errors';

// Verify environment variables are loaded
console.log('Checking environment variables...');
if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_KEY) {
  console.error('Environment variables:', {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    key: process.env.NEXT_PUBLIC_SUPABASE_KEY
  });
  throw new Error('Required environment variables are missing');
}

async function testDataIngestion() {
  try {
    console.log('Starting test data ingestion...');
    
    const ingestionService = new DataIngestionService();
    
    console.log('Testing data ingestion...');
    await ingestionService.ingestAllData();
    
    console.log('Generating mega metrics...');
    await generateMegaMetrics();
    
    console.log('Test data ingestion completed successfully');
  } catch (error: unknown) {
    const err = error as ErrorWithDetails;
    console.error('Error during test data ingestion:', {
      name: err.name || 'Unknown Error',
      message: err.message || 'An unknown error occurred',
      stack: err.stack,
      details: err.details
    });
    throw err;
  }
}

async function generateMegaMetrics() {
  // Get the latest protocol data
  const { data: protocolData, error: protocolError } = await supabase
    .from('protocol_metrics')
    .select('*')
    .order('timestamp', { ascending: false })
    .limit(100);

  if (protocolError) throw protocolError;

  // Generate mega metrics for each protocol
  for (const protocol of protocolData) {
    const megaMetrics = {
      protocol_name: protocol.name,
      primitive_type: determinePrimitiveType(protocol.name),
      tvl_7d_avg: protocol.tvl, // You would actually calculate this from historical data
      tvl_change_7d_pct: 0, // Calculate from historical data
      volume_7d_avg: protocol.volume24h * 7, // Simplified calculation
      volume_change_7d_pct: 0, // Calculate from historical data
      
      // Risk metrics (example values - you would calculate these)
      risk_score: 75.5,
      security_score: 85.0,
      decentralization_score: 70.0,
      
      // Market position
      market_dominance_pct: 5.0,
      competitive_advantage: ['Strong community', 'Technical innovation'],
      market_trend: 'Neutral',
      
      // User metrics
      user_growth_rate_30d: 2.5,
      user_retention_rate_30d: 80.0,
      avg_user_activity_score: 65.0,
      
      // Financial health
      revenue_sustainability_score: 80.0,
      fee_structure_efficiency: 75.0,
      treasury_health_score: 85.0,
      
      // Technical analysis
      technical_reliability_score: 90.0,
      smart_contract_risk_level: 'Low',
      integration_complexity_score: 65.0,
      
      // AI insights
      key_insights: [
        'Strong growth in user adoption',
        'Improving revenue sustainability'
      ],
      growth_opportunities: [
        'Cross-chain expansion',
        'New product features'
      ],
      risk_factors: [
        'Market volatility',
        'Regulatory uncertainty'
      ],
      competitive_analysis: {
        strengths: ['Technical innovation', 'User experience'],
        weaknesses: ['Market penetration', 'Geographic reach']
      },
      market_positioning: {
        segment: 'DeFi',
        target_market: 'Retail traders',
        unique_value_prop: 'Low fees and high security'
      },
      
      // Sentiment analysis
      social_sentiment_score: 78.5,
      developer_activity_score: 85.0,
      community_engagement_score: 82.0,
      
      // Governance metrics
      governance_participation_rate: 15.5,
      proposal_success_rate: 80.0,
      voter_diversity_score: 70.0,
      
      // Innovation metrics
      innovation_score: 85.0,
      feature_competitiveness_score: 80.0,
      adaptation_speed_score: 75.0,
      
      // Metadata
      timestamp: new Date(),
      data_confidence_score: 85.0,
      analysis_version: '1.0.0'
    };

    const { error: insertError } = await supabase
      .from('protocol_mega_metrics')
      .insert([megaMetrics]);

    if (insertError) throw insertError;
  }
}

function determinePrimitiveType(protocolName: string): string {
  // This is a simplified version - you would want more sophisticated logic
  const dexes = ['uniswap', 'sushiswap', 'pancakeswap'];
  const lending = ['aave', 'compound', 'maker'];
  const derivatives = ['gmx', 'dydx', 'perpetual'];
  const yieldProtocols = ['yearn', 'convex', 'curve'];
  const bridges = ['stargate', 'hop', 'across'];
  
  protocolName = protocolName.toLowerCase();
  
  if (dexes.some(dex => protocolName.includes(dex))) return 'DEX';
  if (lending.some(l => protocolName.includes(l))) return 'Lending';
  if (derivatives.some(d => protocolName.includes(d))) return 'Derivatives';
  if (yieldProtocols.some(y => protocolName.includes(y))) return 'Yield';
  if (bridges.some(b => protocolName.includes(b))) return 'Bridge';
  
  return 'Other';
}

// Run the test
if (require.main === module) {
  testDataIngestion()
    .then(() => {
      console.log('Test completed successfully');
      process.exit(0);
    })
    .catch((error: unknown) => {
      const err = error as ErrorWithDetails;
      console.error('Test failed:', {
        name: err.name || 'Unknown Error',
        message: err.message || 'An unknown error occurred',
        stack: err.stack,
        details: err.details
      });
      process.exit(1);
    });
}

export { testDataIngestion }; 