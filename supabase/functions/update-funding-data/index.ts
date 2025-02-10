import { createClient } from '@supabase/supabase-js';
import { getFundingData } from '../utils/funding'; // You'll need to implement this

// This function will run every hour
Deno.cron("update-funding-data", "0 * * * *", async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  try {
    // Get latest funding data from your sources
    const { rates, stats } = await getFundingData();

    // Update market snapshots
    const { error: snapshotsError } = await supabase
      .from('funding_market_snapshots')
      .upsert(rates);

    if (snapshotsError) throw snapshotsError;

    // Update funding statistics
    const { error: statsError } = await supabase
      .from('funding_statistics')
      .upsert(stats);

    if (statsError) throw statsError;

    console.log('Successfully updated funding data');
  } catch (error) {
    console.error('Error updating funding data:', error);
  }
}); 