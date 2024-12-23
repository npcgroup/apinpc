# Hyperliquid Perpetuals

## Overview

Access comprehensive perpetual futures data from Hyperliquid. Our integration provides:

- Real-time market data and prices
- Position tracking and margin information
- Funding rate history and predictions
- Cross-venue funding rate comparisons

## Endpoints

### Get Market Metadata 

typescript
GET /v1/perpetuals/hyperliquid/meta
Access perpetual market configuration:
typescript
// Get market metadata
const response = await fetch('https://api.hyperliquid.xyz/info', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ type: 'meta' })
});
// Response format
{
universe: [{
name: string, // Asset symbol
szDecimals: number, // Size decimals
maxLeverage: number, // Maximum allowed leverage
onlyIsolated: boolean // Whether only isolated margin is supported
}]
}
typescript
GET /v1/perpetuals/hyperliquid/markets
typescript
// Get market state
const response = await fetch('https://api.hyperliquid.xyz/info', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ type: 'metaAndAssetCtxs' })
});
// Response format
{
markets: [{
dayNtlVlm: string, // 24h volume
funding: string, // Current funding rate
impactPxs: string[], // Impact bid/ask prices
markPx: string, // Mark price
midPx: string, // Mid price
openInterest: string, // Open interest
oraclePx: string, // Oracle price
premium: string, // Premium index
prevDayPx: string // Previous day price
}]
}
typescript
GET /v1/perpetuals/hyperliquid/positions/{address}
typescript
// Get user positions
const response = await fetch('https://api.hyperliquid.xyz/info', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
type: 'clearinghouseState',
user: '0x...'
})
});
// Response format
{
assetPositions: [{
position: {
coin: string,
entryPx: string,
leverage: {
type: 'cross' | 'isolated',
value: number
},
liquidationPx: string,
marginUsed: string,
positionValue: string,
szi: string,
unrealizedPnl: string
}
}],
marginSummary: {
accountValue: string,
totalMarginUsed: string,
totalNtlPos: string
}
}
typescript
GET /v1/perpetuals/hyperliquid/funding/{coin}
typescript
// Get funding history
const response = await fetch('https://api.hyperliquid.xyz/info', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
type: 'fundingHistory',
coin: 'ETH',
startTime: 1681222254710
})
});
// Response format
[{
coin: string,
fundingRate: string,
premium: string,
time: number
}]
typescript
class HyperliquidAPI {
private baseUrl = 'https://api.hyperliquid.xyz';
async getMarketState() {
const response = await fetch(${this.baseUrl}/info, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ type: 'metaAndAssetCtxs' })
});
return response.json();
}
async getUserPositions(address: string) {
const response = await fetch(${this.baseUrl}/info, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
type: 'clearinghouseState',
user: address
})
});
return response.json();
}
async getFundingHistory(coin: string, startTime: number) {
const response = await fetch(${this.baseUrl}/info, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
type: 'fundingHistory',
coin,
startTime
})
});
return response.json();
}
}
)
This documentation follows the existing structure while incorporating Hyperliquid-specific details. It provides comprehensive coverage of the perpetuals API endpoints, including market data, user positions, and funding rates.
The documentation should be referenced in the main perpetuals README.md file by adding Hyperliquid to the list of supported data sources and linking to this new documentation.
