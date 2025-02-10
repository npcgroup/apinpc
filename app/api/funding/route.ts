import { NextResponse } from 'next/server'
import { FundingService } from '../../services/fundingService'
import { DataTransformService } from '../../services/dataTransformService'
import { createOpportunityScatter, createExchangeComparison, createFundingHeatmap } from '../../utils/visualizations'

export async function GET() {
  try {
    let fundingService: FundingService;
    
    try {
      fundingService = new FundingService();
    } catch (initError) {
      console.error('Failed to initialize FundingService:', initError);
      return NextResponse.json(
        { error: 'Service configuration error. Please check environment variables.' },
        { status: 500 }
      );
    }

    const ratesData = await fundingService.getPredictedRates();
    const latestStats = await fundingService.getLatestStats();

    // Transform the data
    const directionalOpps = DataTransformService.processDirectionalOpportunities(ratesData.rates);
    const crossExchangeOpps = DataTransformService.processCrossExchangeOpportunities(ratesData.rates);
    const detailedView = DataTransformService.processDetailedView(ratesData.rates);

    // Create visualizations
    const vizData = {
      opportunity_scatter: createOpportunityScatter(ratesData.rates),
      exchange_comparison: createExchangeComparison(ratesData.rates),
      funding_heatmap: createFundingHeatmap(ratesData.rates),
      top_opportunities: directionalOpps
    };

    return NextResponse.json({
      stats: latestStats,
      opportunities: {
        directional: directionalOpps,
        crossExchange: crossExchangeOpps
      },
      analysis: vizData,
      detailed: detailedView
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch funding data' },
      { status: 500 }
    );
  }
} 