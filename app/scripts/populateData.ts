import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

async function populateInitialData() {
  // Sample funding market snapshots
  const marketSnapshots = [
    {
      symbol: 'BTC-PERP',
      exchange: 'Binance',
      funding_rate: 0.0001,
      predicted_rate: 0.00012,
      rate_diff: 0.00002,
      time_to_funding: 8,
      direction: 'Long',
      annualized_rate: 0.0365,
      opportunity_score: 85,
      mark_price: 45000,
      suggested_position: 'Long',
      created_at: new Date().toISOString()
    },
    {
      symbol: 'ETH-PERP',
      exchange: 'Hyperliquid',
      funding_rate: -0.0002,
      predicted_rate: -0.00025,
      rate_diff: 0.00005,
      time_to_funding: 8,
      direction: 'Short',
      annualized_rate: -0.0730,
      opportunity_score: 78,
      mark_price: 2500,
      suggested_position: 'Short',
      created_at: new Date().toISOString()
    },
    // Add more market snapshots as needed
  ];

  // Sample funding statistics
  const fundingStats = {
    total_markets: 150,
    binance_markets: 90,
    hl_markets: 60,
    hourly_rate: 0.0001,
    eight_hour_rate: 0.0008,
    daily_rate: 0.0024,
    created_at: new Date().toISOString()
  };

  try {
    // Insert market snapshots
    const { error: snapshotsError } = await supabase
      .from('funding_market_snapshots')
      .upsert(marketSnapshots);

    if (snapshotsError) {
      console.error('Error inserting market snapshots:', snapshotsError);
      return;
    }

    // Insert funding statistics
    const { error: statsError } = await supabase
      .from('funding_statistics')
      .upsert(fundingStats);

    if (statsError) {
      console.error('Error inserting funding statistics:', statsError);
      return;
    }

    console.log('Successfully populated initial data!');
  } catch (error) {
    console.error('Error populating data:', error);
  }
}

// Run the population script
populateInitialData(); 