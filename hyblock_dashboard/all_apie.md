Orderbook


GET
/asksIncreaseDecrease


GET
/bidAsk


GET
/bidsIncreaseDecrease


GET
/bidAskRatio


GET
/bidAskDelta


GET
/bidAskRatioDiff


GET
/combinedBook


GET
/bidsAskSpread

Options


GET
/bvol


GET
/dvol

Orderflow


GET
/botTracker


GET
/buyVolume


GET
/klines


GET
/sellVolume


GET
/volumeDelta


GET
/anchoredCVD


GET
/marketOrderCount


GET
/limitOrderCount


GET
/marketOrderAverageSize


GET
/limitOrderAverageSize


GET
/pdLevels


GET
/pwLevels


GET
/pmLevels


GET
/slippage


GET
/transferofcontracts


GET
/participationratio

Open Interest


GET
/openInterest


GET
/openInterestDelta


GET
/anchoredOIDelta

Liquidity


GET
/cumulativeLiqLevel


GET
/liquidationLevels


GET
/liquidation


GET
/liquidationHeatmap


GET
/averageLeverageUsed


GET
/averageLeverageDelta


GET
/anchoredLLC


GET
/anchoredLLS


GET
/anchoredCLLCD


GET
/anchoredCLLSD

Funding Rate


GET
/fundingRate

Longs and Shorts


GET
/binanceGlobalAccounts


GET
/anchoredBinanceGlobalAccounts


GET
/binanceTopTraderAccounts


GET
/anchoredBinanceTopTraderAccounts


GET
/binanceTopTraderPositions


GET
/anchoredBinanceTopTraderPositions


GET
/binanceTrueRetailLongShort


GET
/binanceWhaleRetailDelta


GET
/anchoredBinanceWhaleRetailDelta


GET
/traderSentimentGap


GET
/whalePositionDominance


GET
/bybitGlobalAccounts


GET
/huobiTopTraderAccounts


GET
/huobiTopTraderAccountsQuarterly


GET
/huobiTopTraderPositions


GET
/huobiTopTraderPositionsQuarterly


GET
/netLongShort


GET
/anchoredCLS


GET
/netLongShortDelta


GET
/anchoredCLSD


GET
/okxGlobalAccounts


GET
/okxTopTraderAccounts


GET
/okxWhaleRetailDelta

Sentiment


GET
/bitmexLeaderboardNotionalProfit


GET
/bitmexLeaderboardROEProfit


GET
/fearAndGreed


GET
/marginLendingRatio


GET
/trollbox


GET
/userBotRatio


GET
/stablecoinPremiumP2P


GET
/wbtcMintBurn

Profile Tool


GET
/openInterestProfile


GET
/volumeProfile

Catalog


GET
/catalog

apiUsage


Models
asksIncreaseDecrease{
openDate	integer
example: 1724223600
asks_increase_decrease	number
example: 5048640.743506074
}
bidAsk{
openDate	integer
example: 1724223600
ask	number
example: 347768395.98476046
bid	number
example: 481190189.74814093
}
bidsIncreaseDecrease{
openDate	integer
example: 1724246280
bids_increase_decrease	number
example: 31868487.71439886
}
bidAskRatio{
openDate	integer
example: 1665047820
bidAskRatio	number
example: 0.14752672038637354
}
bidAskDelta{
openDate	integer
example: 1695711720
bidAskDelta	number
example: -35945460.68240702
}
bidAskRatioDiff{
openDate	integer
example: 1665047820
bidAskRatioDiff	number
example: -163215377.8376366
}
combinedBook{
openDate	integer
example: 1695717720
combinedBook	number
example: 589398610.0514098
}
bvol{
openDate	integer
example: 1695892500
open	number
example: 39.83476124
high	number
example: 39.88290896
low	number
example: 39.83478107
close	number
example: 39.88290896
}
dvol{
openDate	integer
example: 1695893940
open	number
example: 38.52
high	number
example: 38.52
low	number
example: 38.49
close	number
example: 38.49
}
botTracker{
openDate	integer
example: 1691658180
Total	number
example: 3
Buy	number
example: 3
Sell	number
example: 0
Delta	number
example: 3
}
buyVolume{
openDate	integer
example: 1665047820
buyVolume	number
example: 39101.67570000001
}
klines{
openDate	integer
example: 1692344580
open	number
example: 56.31
close	number
example: 56.27
high	number
example: 56.32
low	number
example: 56.27
}
sellVolume{
openDate	integer
example: 1665047820
sellVolume	number
example: 1798220.5481000019
}
volumeDelta{
openDate	integer
example: 1665047820
volumeDelta	number
example: 1798220.5481000019
}
anchoredCVD{
openDate	integer
example: 1731582000
cumulativeDelta	number
example: 37988.11845679252
}
marketOrderCount{
openDate	integer
example: 1676286000
buy	number
example: 530
sell	number
example: 535
total	number
example: 1065
delta	number
example: -5
}
limitOrderCount{
openDate	integer
example: 1695208500
buy	number
example: 402
sell	number
example: 256
total	number
example: 658
delta	number
example: 146
}
marketOrderAverageSize{
openDate	integer
example: 1676286000
buy	number
example: 530
sell	number
example: 535
total	number
example: 1065
delta	number
example: -5
}
limitOrderAverageSize{
openDate	integer
example: 1695210120
buy	number
example: 63.125
sell	number
example: 488.5
total	number
example: 148.2
delta	number
example: -425.375
}
pdLevels{
openDate	integer
example: 1691366700
pdOpen	number
example: 29075.9
pdHigh	number
example: 29274.5
pdLow	number
example: 28682.3
pdEq	number
example: 28978.4
}
pwLevels{
openDate	integer
example: 1724025600
pdOpen	number
example: 58693.1
pdHigh	number
example: 61839.7
pdLow	number
example: 55969
pdEq	number
example: 58904.35
}
pmLevels{
openDate	integer
example: 1719792000
pdOpen	number
example: 67577.9
pdHigh	number
example: 72144
pdLow	number
example: 58218
pdEq	number
example: 65181
}
slippage{
openDate	integer
example: 1676286000
max	number
example: 53
averageMax	number
example: 123
total	number
example: -56
}
openInterest{
openDate	integer
example: 1665047820
open	number
example: 3298101915.6755
low	number
example: 3297517559.4792995
high	number
example: 3297517559.4792995
close	number
example: 3297517559.4792995
}
openInterestDelta
anchoredOIDelta
cumulativeLiqLevel
liquidationLevels
liquidation
liquidationHeatmap
averageLeverageUsed
averageLeverageDelta
fundingRate
binanceGlobalAccounts
anchoredBinanceGlobalAccounts
binanceTopTraderAccounts
anchoredBinanceTopTraderAccounts
binanceTopTraderPositions
anchoredBinanceTopTraderPositions
binanceTrueRetailLongShort
binanceWhaleRetailDelta
anchoredBinanceWhaleRetailDelta
traderSentimentGap
whalePositionDominance
bybitGlobalAccounts
huobiTopTraderAccounts
huobiTopTraderAccountsQuarterly
huobiTopTraderPositions
huobiTopTraderPositionsQuarterly
netLongShort
anchoredCLS
netLongShortDelta
anchoredCLSD
okxGlobalAccounts
okxTopTraderAccounts
okxWhaleRetailDelta
bitmexLeaderboardNotionalProfit
bitmexLeaderboardROEProfit
fearAndGreed
marginLendingRatio
trollbox
userBotRatio
stablecoinPremiumP2P
wbtcMintBurn
openInterestProfile{
startDate	integer
example: 1678755600
endDate	integer
example: 1678842000
currentPrice	number
example: 0.4039
data	[...]
}
volumeProfile
transferofcontracts
participationratio
catalog
bidsAskSpread
anchoredLLC
anchoredCLLCD
anchoredLLS{
openDate	integer
example: 1698326940
totalSize	number
example: 13639435230.2304
}
anchoredCLLSD{
openDate	integer
example: 1698326940
totalSize	number
example: 13639435230.2304
}
remainingHitBalance
Error400
Error401
Error403
Error404
Error429
Error500