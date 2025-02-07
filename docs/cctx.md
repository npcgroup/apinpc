hyperliquid
Kind: global class
Extends: Exchange

fetchCurrencies
fetchMarkets
fetchMarkets
fetchMarkets
fetchBalance
fetchOrderBook
fetchTickers
fetchFundingRates
fetchOHLCV
fetchTrades
createOrder
createOrders
createOrders
cancelOrder
cancelOrders
cancelOrdersForSymbols
cancelAllOrdersAfter
editOrder
fetchFundingRateHistory
fetchOpenOrders
fetchClosedOrders
fetchCanceledOrders
fetchCanceledAndClosedOrders
fetchOrders
fetchOrder
fetchMyTrades
fetchPosition
fetchPositions
setMarginMode
setLeverage
addMargin
reduceMargin
transfer
withdraw
fetchTradingFee
fetchLedger
fetchDeposits
fetchWithdrawals
createOrdersWs
createOrder
editOrder
watchOrderBook
unWatchOrderBook
watchTicker
watchTickers
unWatchTickers
watchMyTrades
unWatchTrades
watchOHLCV
unWatchOHLCV
watchOrders

fetchCurrencies
fetches all available currencies on an exchange

Kind: instance method of hyperliquid
Returns: object - an associative dictionary of currencies

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-metadata

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchCurrencies ([params])
Copy to clipboardErrorCopied

fetchMarkets
retrieves data on all markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-spot-asset-contexts
Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchMarkets ([params])
Copy to clipboardErrorCopied

fetchMarkets
retrieves data on all swap markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchMarkets ([params])
Copy to clipboardErrorCopied

fetchMarkets
retrieves data on all spot markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-spot-asset-contexts

Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchMarkets ([params])
Copy to clipboardErrorCopied

fetchBalance
query for balance and get the amount of funds available for trading or funds locked in orders

Kind: instance method of hyperliquid
Returns: object - a balance structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-a-users-token-balances
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-users-perpetuals-account-summary
Param	Type	Required	Description
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
params.type	string	No	wallet type, ['spot', 'swap'], defaults to swap
hyperliquid.fetchBalance ([params])
Copy to clipboardErrorCopied

fetchOrderBook
fetches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of hyperliquid
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#l2-book-snapshot

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

fetchTickers
fetches price tickers for multiple markets, statistical information calculated over the past 24 hours for each market

Kind: instance method of hyperliquid
Returns: object - a dictionary of ticker structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot#retrieve-spot-asset-contexts
Param	Type	Required	Description
symbols	Array<string>	No	unified symbols of the markets to fetch the ticker for, all market tickers are returned if not assigned
params	object	No	extra parameters specific to the exchange API endpoint
params.type	string	No	'spot' or 'swap', by default fetches both
hyperliquid.fetchTickers ([symbols, params])
Copy to clipboardErrorCopied

fetchFundingRates
retrieves data on all swap markets for hyperliquid

Kind: instance method of hyperliquid
Returns: Array<object> - an array of objects representing market data

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-perpetuals-asset-contexts-includes-mark-price-current-funding-open-interest-etc

Param	Type	Required	Description
symbols	Array<string>	No	list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.fetchFundingRates ([symbols, params])
Copy to clipboardErrorCopied

fetchOHLCV
fetches historical candlestick data containing the open, high, low, and close price, and the volume of a market

Kind: instance method of hyperliquid
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#candle-snapshot

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents, support '1m', '15m', '1h', '1d'
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest candle to fetch
hyperliquid.fetchOHLCV (symbol, timeframe[, since, limit, params])
Copy to clipboardErrorCopied

fetchTrades
get the list of most recent trades for a particular symbol

Kind: instance method of hyperliquid
Returns: Array<Trade> - a list of trade structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills-by-time
Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trades structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest trade
params.address	string	No	wallet address that made trades
params.user	string	No	wallet address that made trades
hyperliquid.fetchTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

createOrder
create a trade order

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.slippage	string	No	the slippage for market order
params.vaultAddress	string	No	the vault address for order
hyperliquid.createOrder (symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

createOrders
create a list of trade orders

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
orders	Array	Yes	list of orders to create, each object should contain the parameters required by createOrder, namely symbol, type, side, amount, price and params
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.createOrders (orders[, params])
Copy to clipboardErrorCopied

createOrders
create a list of trade orders

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Description
orders	Array	list of orders to create, each object should contain the parameters required by createOrder, namely symbol, type, side, amount, price and params
hyperliquid.createOrders (orders, [undefined])
Copy to clipboardErrorCopied

cancelOrder
cancels an open order

Kind: instance method of hyperliquid
Returns: object - An order structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s-by-cloid
Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address for order
hyperliquid.cancelOrder (id, symbol[, params])
Copy to clipboardErrorCopied

cancelOrders
cancel multiple orders

Kind: instance method of hyperliquid
Returns: object - an list of order structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s-by-cloid
Param	Type	Required	Description
ids	Array<string>	Yes	order ids
symbol	string	No	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
params.clientOrderId	string, Array<string>	No	client order ids, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address
hyperliquid.cancelOrders (ids[, symbol, params])
Copy to clipboardErrorCopied

cancelOrdersForSymbols
cancel multiple orders for multiple symbols

Kind: instance method of hyperliquid
Returns: object - an list of order structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#cancel-order-s-by-cloid
Param	Type	Required	Description
orders	Array<CancellationRequest>	Yes	each order should contain the parameters required by cancelOrder namely id and symbol, example [{"id": "a", "symbol": "BTC/USDT"}, {"id": "b", "symbol": "ETH/USDT"}]
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address
hyperliquid.cancelOrdersForSymbols (orders[, params])
Copy to clipboardErrorCopied

cancelAllOrdersAfter
dead man's switch, cancel all orders after the given timeout

Kind: instance method of hyperliquid
Returns: object - the api result

Param	Type	Required	Description
timeout	number	Yes	time in milliseconds, 0 represents cancel the timer
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address
hyperliquid.cancelAllOrdersAfter (timeout[, params])
Copy to clipboardErrorCopied

editOrder
edit a trade order

Kind: instance method of hyperliquid
Returns: object - an order structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-an-order
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-multiple-orders
Param	Type	Required	Description
id	string	Yes	cancel order id
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address for order
hyperliquid.editOrder (id, symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

fetchFundingRateHistory
fetches historical funding rate prices

Kind: instance method of hyperliquid
Returns: Array<object> - a list of funding rate structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-historical-funding-rates

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the funding rate history for
since	int	No	timestamp in ms of the earliest funding rate to fetch
limit	int	No	the maximum amount of funding rate structures to fetch
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest funding rate
hyperliquid.fetchFundingRateHistory (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOpenOrders
fetch all unfilled currently open orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-open-orders

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
params.method	string	No	'openOrders' or 'frontendOpenOrders' default is 'frontendOpenOrders'
hyperliquid.fetchOpenOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchClosedOrders
fetch all unfilled currently closed orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchClosedOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchCanceledOrders
fetch all canceled orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchCanceledOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchCanceledAndClosedOrders
fetch all closed and canceled orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchCanceledAndClosedOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOrders
fetch all orders

Kind: instance method of hyperliquid
Returns: Array<Order> - a list of order structures

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch open orders for
limit	int	No	the maximum number of open orders structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchOrder
fetches information on an order made by the user

Kind: instance method of hyperliquid
Returns: object - An order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#query-order-status-by-oid-or-cloid

Param	Type	Required	Description
id	string	Yes	order id
symbol	string	Yes	unified symbol of the market the order was made in
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchOrder (id, symbol[, params])
Copy to clipboardErrorCopied

fetchMyTrades
fetch all trades made by the user

Kind: instance method of hyperliquid
Returns: Array<Trade> - a list of trade structures

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#retrieve-a-users-fills-by-time
Param	Type	Required	Description
symbol	string	Yes	unified market symbol
since	int	No	the earliest time in ms to fetch trades for
limit	int	No	the maximum number of trades structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest trade
hyperliquid.fetchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

fetchPosition
fetch data on an open position

Kind: instance method of hyperliquid
Returns: object - a position structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-users-perpetuals-account-summary

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market the position is held in
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchPosition (symbol[, params])
Copy to clipboardErrorCopied

fetchPositions
fetch all open positions

Kind: instance method of hyperliquid
Returns: Array<object> - a list of position structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals#retrieve-users-perpetuals-account-summary

Param	Type	Required	Description
symbols	Array<string>	No	list of unified market symbols
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchPositions ([symbols, params])
Copy to clipboardErrorCopied

setMarginMode
set margin mode (symbol)

Kind: instance method of hyperliquid
Returns: object - response from the exchange

Param	Type	Required	Description
marginMode	string	Yes	margin mode must be either [isolated, cross]
symbol	string	Yes	unified market symbol of the market the position is held in, default is undefined
params	object	No	extra parameters specific to the exchange API endpoint
params.leverage	string	No	the rate of leverage, is required if setting trade mode (symbol)
hyperliquid.setMarginMode (marginMode, symbol[, params])
Copy to clipboardErrorCopied

setLeverage
set the level of leverage for a market

Kind: instance method of hyperliquid
Returns: object - response from the exchange

Param	Type	Required	Description
leverage	float	Yes	the rate of leverage
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
params.marginMode	string	No	margin mode must be either [isolated, cross], default is cross
hyperliquid.setLeverage (leverage, symbol[, params])
Copy to clipboardErrorCopied

addMargin
add margin

Kind: instance method of hyperliquid
Returns: object - a margin structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#update-isolated-margin

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
amount	float	Yes	amount of margin to add
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.addMargin (symbol, amount[, params])
Copy to clipboardErrorCopied

reduceMargin
remove margin from a position

Kind: instance method of hyperliquid
Returns: object - a margin structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#update-isolated-margin

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
amount	float	Yes	the amount of margin to remove
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.reduceMargin (symbol, amount[, params])
Copy to clipboardErrorCopied

transfer
transfer currency internally between wallets on the same account

Kind: instance method of hyperliquid
Returns: object - a transfer structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#l1-usdc-transfer

Param	Type	Required	Description
code	string	Yes	unified currency code
amount	float	Yes	amount to transfer
fromAccount	string	Yes	account to transfer from spot, swap
toAccount	string	Yes	account to transfer to swap, spot or address
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	the vault address for order
hyperliquid.transfer (code, amount, fromAccount, toAccount[, params])
Copy to clipboardErrorCopied

withdraw
make a withdrawal (only support USDC)

Kind: instance method of hyperliquid
Returns: object - a transaction structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#initiate-a-withdrawal-request
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#deposit-or-withdraw-from-a-vault
Param	Type	Required	Description
code	string	Yes	unified currency code
amount	float	Yes	the amount to withdraw
address	string	Yes	the address to withdraw to
tag	string	Yes	
params	object	No	extra parameters specific to the exchange API endpoint
params.vaultAddress	string	No	vault address withdraw from
hyperliquid.withdraw (code, amount, address, tag[, params])
Copy to clipboardErrorCopied

fetchTradingFee
fetch the trading fees for a market

Kind: instance method of hyperliquid
Returns: object - a fee structure

Param	Type	Required	Description
symbol	string	Yes	unified market symbol
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.fetchTradingFee (symbol[, params])
Copy to clipboardErrorCopied

fetchLedger
fetch the history of changes, actions done by the user or operations that altered the balance of the user

Kind: instance method of hyperliquid
Returns: object - a ledger structure

Param	Type	Required	Description
code	string	No	unified currency code
since	int	No	timestamp in ms of the earliest ledger entry
limit	int	No	max number of ledger entries to return
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	timestamp in ms of the latest ledger entry
hyperliquid.fetchLedger ([code, since, limit, params])
Copy to clipboardErrorCopied

fetchDeposits
fetch all deposits made to an account

Kind: instance method of hyperliquid
Returns: Array<object> - a list of transaction structures

Param	Type	Required	Description
code	string	Yes	unified currency code
since	int	No	the earliest time in ms to fetch deposits for
limit	int	No	the maximum number of deposits structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	the latest time in ms to fetch withdrawals for
hyperliquid.fetchDeposits (code[, since, limit, params])
Copy to clipboardErrorCopied

fetchWithdrawals
fetch all withdrawals made from an account

Kind: instance method of hyperliquid
Returns: Array<object> - a list of transaction structures

Param	Type	Required	Description
code	string	Yes	unified currency code
since	int	No	the earliest time in ms to fetch withdrawals for
limit	int	No	the maximum number of withdrawals structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.until	int	No	the latest time in ms to fetch withdrawals for
hyperliquid.fetchWithdrawals (code[, since, limit, params])
Copy to clipboardErrorCopied

createOrdersWs
create a list of trade orders using WebSocket post request

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
orders	Array	Yes	list of orders to create, each object should contain the parameters required by createOrder, namely symbol, type, side, amount, price and params
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.createOrdersWs (orders[, params])
Copy to clipboardErrorCopied

createOrder
create a trade order using WebSocket post request

Kind: instance method of hyperliquid
Returns: object - an order structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#place-an-order

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.slippage	string	No	the slippage for market order
params.vaultAddress	string	No	the vault address for order
hyperliquid.createOrder (symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

editOrder
edit a trade order

Kind: instance method of hyperliquid
Returns: object - an order structure

See

https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-an-order
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint#modify-multiple-orders
Param	Type	Required	Description
id	string	Yes	cancel order id
symbol	string	Yes	unified symbol of the market to create an order in
type	string	Yes	'market' or 'limit'
side	string	Yes	'buy' or 'sell'
amount	float	Yes	how much of currency you want to trade in units of base currency
price	float	No	the price at which the order is to be fulfilled, in units of the quote currency, ignored in market orders
params	object	No	extra parameters specific to the exchange API endpoint
params.timeInForce	string	No	'Gtc', 'Ioc', 'Alo'
params.postOnly	bool	No	true or false whether the order is post-only
params.reduceOnly	bool	No	true or false whether the order is reduce-only
params.triggerPrice	float	No	The price at which a trigger order is triggered at
params.clientOrderId	string	No	client order id, (optional 128 bit hex string e.g. 0x1234567890abcdef1234567890abcdef)
params.vaultAddress	string	No	the vault address for order
hyperliquid.editOrder (id, symbol, type, side, amount[, price, params])
Copy to clipboardErrorCopied

watchOrderBook
watches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of hyperliquid
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
limit	int	No	the maximum amount of order book entries to return
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.watchOrderBook (symbol[, limit, params])
Copy to clipboardErrorCopied

unWatchOrderBook
unWatches information on open orders with bid (buy) and ask (sell) prices, volumes and other data

Kind: instance method of hyperliquid
Returns: object - A dictionary of order book structures indexed by market symbols

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the order book for
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.unWatchOrderBook (symbol[, params])
Copy to clipboardErrorCopied

watchTicker
watches a price ticker, a statistical calculation with the information calculated over the past 24 hours for a specific market

Kind: instance method of hyperliquid
Returns: object - a ticker structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.watchTicker (symbol[, params])
Copy to clipboardErrorCopied

watchTickers
watches a price ticker, a statistical calculation with the information calculated over the past 24 hours for all markets of a specific list

Kind: instance method of hyperliquid
Returns: object - a ticker structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbols	Array<string>	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.watchTickers (symbols[, params])
Copy to clipboardErrorCopied

unWatchTickers
unWatches a price ticker, a statistical calculation with the information calculated over the past 24 hours for all markets of a specific list

Kind: instance method of hyperliquid
Returns: object - a ticker structure

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbols	Array<string>	Yes	unified symbol of the market to fetch the ticker for
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.unWatchTickers (symbols[, params])
Copy to clipboardErrorCopied

watchMyTrades
watches information on multiple trades made by the user

Kind: instance method of hyperliquid
Returns: Array<object> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.watchMyTrades (symbol[, since, limit, params])
Copy to clipboardErrorCopied

unWatchTrades
unWatches information on multiple trades made in a market

Kind: instance method of hyperliquid
Returns: Array<object> - a list of trade structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market trades were made in
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.unWatchTrades (symbol[, params])
Copy to clipboardErrorCopied

watchOHLCV
watches historical candlestick data containing the open, high, low, close price, and the volume of a market

Kind: instance method of hyperliquid
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
since	int	No	timestamp in ms of the earliest candle to fetch
limit	int	No	the maximum amount of candles to fetch
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.watchOHLCV (symbol, timeframe[, since, limit, params])
Copy to clipboardErrorCopied

unWatchOHLCV
watches historical candlestick data containing the open, high, low, close price, and the volume of a market

Kind: instance method of hyperliquid
Returns: Array<Array<int>> - A list of candles ordered as timestamp, open, high, low, close, volume

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified symbol of the market to fetch OHLCV data for
timeframe	string	Yes	the length of time each candle represents
params	object	No	extra parameters specific to the exchange API endpoint
hyperliquid.unWatchOHLCV (symbol, timeframe[, params])
Copy to clipboardErrorCopied

watchOrders
watches information on multiple orders made by the user

Kind: instance method of hyperliquid
Returns: Array<object> - a list of order structures

See: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions

Param	Type	Required	Description
symbol	string	Yes	unified market symbol of the market orders were made in
since	int	No	the earliest time in ms to fetch orders for
limit	int	No	the maximum number of order structures to retrieve
params	object	No	extra parameters specific to the exchange API endpoint
params.user	string	No	user address, will default to this.walletAddress if not provided
hyperliquid.watchOrders (symbol[, since, limit, params])
Copy to clipboardErrorCopied
