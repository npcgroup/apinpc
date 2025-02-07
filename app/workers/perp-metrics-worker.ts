import { createClient } from '@supabase/supabase-js';
import { fetchPerpData } from '../utils/ccxt-client';
import type { Database } from '@/types/supabase';

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
);

export async function updatePerpMetrics() {
  try {
    console.log('Starting perp metrics update...');
    
    // Get latest data from CCXT
    const perpData = await fetchPerpData();
    
    if (!perpData.length) {
      console.error('No perp data fetched');
      throw new Error('No perp data fetched');
    }

    // For each market, check if we need to insert new data
    for (const data of perpData) {
      // Check if we have recent data for this market
      const { data: existingData, error: queryError } = await supabase
        .from('funding_rate_snapshots')
        .select('*')
        .eq('token', data.token)
        .eq('exchange', data.exchange)
        .order('timestamp', { ascending: false })
        .limit(1);

      if (queryError) {
        console.error('Error checking existing data:', queryError);
        continue;
      }

      const latestExisting = existingData?.[0];
      const shouldInsert = !latestExisting || 
        new Date(data.timestamp).getTime() - new Date(latestExisting.timestamp).getTime() > 5 * 60 * 1000; // 5 minutes

      if (shouldInsert) {
        const { error: insertError } = await supabase
          .from('funding_rate_snapshots')
          .insert([data]);

        if (insertError) {
          console.error(`Error inserting data for ${data.token}:`, insertError);
        } else {
          console.log(`Updated data for ${data.token} on ${data.exchange}`);
        }
      }
    }
    
    console.log('Successfully updated perp metrics');
    return perpData;
  } catch (error) {
    console.error('Error updating perp metrics:', error);
    throw error;
  }
} 