import { formatDate } from '../utils/dateUtils'; // Create this utility file

export const NFT_QUERIES = {
  topSales: `
    WITH nft_trades AS (
      SELECT
        date_trunc('hour', block_time) as hour,
        nft_token_id as token_id,
        collection,
        amount_usd,
        token_standard,
        trade_type,
        buyer,
        seller,
        tx_hash,
        platform_name
      FROM dune.nft_trades
      WHERE block_time >= NOW() - INTERVAL '24 hours'
        AND amount_usd IS NOT NULL
        AND amount_usd > 0
    )
    SELECT
      hour,
      collection,
      token_id,
      amount_usd as price_usd,
      platform_name as marketplace,
      trade_type,
      buyer,
      seller,
      tx_hash
    FROM nft_trades
    ORDER BY amount_usd DESC
    LIMIT 10;
  `
};

export function formatNFTSalesResponse(data: any[]): string {
  if (!data || data.length === 0) {
    return "No NFT sales found in the last 24 hours.";
  }

  let response = "🎨 Top NFT Sales (Last 24h)\n\n";
  
  data.forEach((sale, index) => {
    const price = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(sale.price_usd);

    response += `${index + 1}. ${sale.collection}\n`;
    response += `   💎 Price: ${price}\n`;
    response += `   🏷️ Token ID: ${sale.token_id}\n`;
    response += `   🏪 Marketplace: ${sale.marketplace}\n`;
    response += `   🕒 Time: ${formatDate(new Date(sale.hour))}\n\n`;
  });

  return response;
} 