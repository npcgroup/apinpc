import type * as types from './types';
import type { ConfigOptions, FetchResponse } from 'api/dist/core'
import Oas from 'oas';
import APICore from 'api/dist/core';
import definition from './openapi.json';

class SDK {
  spec: Oas;
  core: APICore;

  constructor() {
    this.spec = Oas.init(definition);
    this.core = new APICore(this.spec, 'birdeyedotso/1.0.0 (api/6.1.2)');
  }

  /**
   * Optionally configure various options that the SDK allows.
   *
   * @param config Object of supported SDK options and toggles.
   * @param config.timeout Override the default `fetch` request timeout of 30 seconds. This number
   * should be represented in milliseconds.
   */
  config(config: ConfigOptions) {
    this.core.setConfig(config);
  }

  /**
   * If the API you're using requires authentication you can supply the required credentials
   * through this method and the library will magically determine how they should be used
   * within your API request.
   *
   * With the exception of OpenID and MutualTLS, it supports all forms of authentication
   * supported by the OpenAPI specification.
   *
   * @example <caption>HTTP Basic auth</caption>
   * sdk.auth('username', 'password');
   *
   * @example <caption>Bearer tokens (HTTP or OAuth 2)</caption>
   * sdk.auth('myBearerToken');
   *
   * @example <caption>API Keys</caption>
   * sdk.auth('myApiKey');
   *
   * @see {@link https://spec.openapis.org/oas/v3.0.3#fixed-fields-22}
   * @see {@link https://spec.openapis.org/oas/v3.1.0#fixed-fields-22}
   * @param values Your auth credentials for the API; can specify up to two strings or numbers.
   */
  auth(...values: string[] | number[]) {
    this.core.setAuth(...values);
    return this;
  }

  /**
   * If the API you're using offers alternate server URLs, and server variables, you can tell
   * the SDK which one to use with this method. To use it you can supply either one of the
   * server URLs that are contained within the OpenAPI definition (along with any server
   * variables), or you can pass it a fully qualified URL to use (that may or may not exist
   * within the OpenAPI definition).
   *
   * @example <caption>Server URL with server variables</caption>
   * sdk.server('https://{region}.api.example.com/{basePath}', {
   *   name: 'eu',
   *   basePath: 'v14',
   * });
   *
   * @example <caption>Fully qualified server URL</caption>
   * sdk.server('https://eu.api.example.com/v14');
   *
   * @param url Server URL
   * @param variables An object of variables to replace into the server URL.
   */
  server(url: string, variables = {}) {
    this.core.setServer(url, variables);
  }

  /**
   * Get a list of all supported networks.
   *
   * @summary Supported Networks
   * @throws FetchError<400, types.GetDefiNetworksResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiNetworksResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiNetworksResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiNetworksResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiNetworksResponse500> Internal Server Error
   */
  getDefiNetworks(): Promise<FetchResponse<200, types.GetDefiNetworksResponse200>> {
    return this.core.fetch('/defi/networks', 'get');
  }

  /**
   * Get price update of a token.
   *
   * @summary Price
   * @throws FetchError<400, types.GetDefiPriceResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiPriceResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiPriceResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiPriceResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiPriceResponse500> Internal Server Error
   */
  getDefiPrice(metadata: types.GetDefiPriceMetadataParam): Promise<FetchResponse<200, types.GetDefiPriceResponse200>> {
    return this.core.fetch('/defi/price', 'get', metadata);
  }

  /**
   * Get price updates of multiple tokens in a single API call. Maximum 100 tokens
   *
   * @summary Price - Multiple
   * @throws FetchError<400, types.GetDefiMultiPriceResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiMultiPriceResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiMultiPriceResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiMultiPriceResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiMultiPriceResponse500> Internal Server Error
   */
  getDefiMulti_price(metadata: types.GetDefiMultiPriceMetadataParam): Promise<FetchResponse<200, types.GetDefiMultiPriceResponse200>> {
    return this.core.fetch('/defi/multi_price', 'get', metadata);
  }

  /**
   * Get price updates of multiple tokens in a single API call. Maximum 100 tokens
   *
   * @summary Price - Multiple
   * @throws FetchError<400, types.PostDefiMultiPriceResponse400> Bad Request
   * @throws FetchError<401, types.PostDefiMultiPriceResponse401> Unauthorized
   * @throws FetchError<403, types.PostDefiMultiPriceResponse403> Forbidden
   * @throws FetchError<429, types.PostDefiMultiPriceResponse429> Too Many Requests
   * @throws FetchError<500, types.PostDefiMultiPriceResponse500> Internal Server Error
   */
  postDefiMulti_price(body: types.PostDefiMultiPriceBodyParam, metadata?: types.PostDefiMultiPriceMetadataParam): Promise<FetchResponse<200, types.PostDefiMultiPriceResponse200>> {
    return this.core.fetch('/defi/multi_price', 'post', body, metadata);
  }

  /**
   * Get historical price line chart of a token.
   *
   * @summary Price - Historical
   * @throws FetchError<400, types.GetDefiHistoryPriceResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiHistoryPriceResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiHistoryPriceResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiHistoryPriceResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiHistoryPriceResponse500> Internal Server Error
   */
  getDefiHistory_price(metadata: types.GetDefiHistoryPriceMetadataParam): Promise<FetchResponse<200, types.GetDefiHistoryPriceResponse200>> {
    return this.core.fetch('/defi/history_price', 'get', metadata);
  }

  /**
   * Get historical price by unix timestamp
   *
   * @summary Price - Historical by unix time
   * @throws FetchError<400, types.GetDefiHistoricalPriceUnixResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiHistoricalPriceUnixResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiHistoricalPriceUnixResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiHistoricalPriceUnixResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiHistoricalPriceUnixResponse500> Internal Server Error
   */
  getDefiHistorical_price_unix(metadata: types.GetDefiHistoricalPriceUnixMetadataParam): Promise<FetchResponse<200, types.GetDefiHistoricalPriceUnixResponse200>> {
    return this.core.fetch('/defi/historical_price_unix', 'get', metadata);
  }

  /**
   * Get list of trades of a certain token.
   *
   * @summary Trades - Token
   * @throws FetchError<400, types.GetDefiTxsTokenResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTxsTokenResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTxsTokenResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTxsTokenResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTxsTokenResponse500> Internal Server Error
   */
  getDefiTxsToken(metadata: types.GetDefiTxsTokenMetadataParam): Promise<FetchResponse<200, types.GetDefiTxsTokenResponse200>> {
    return this.core.fetch('/defi/txs/token', 'get', metadata);
  }

  /**
   * Get list of trades of a certain pair or market.
   *
   * @summary Trades - Pair
   * @throws FetchError<400, types.GetDefiTxsPairResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTxsPairResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTxsPairResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTxsPairResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTxsPairResponse500> Internal Server Error
   */
  getDefiTxsPair(metadata: types.GetDefiTxsPairMetadataParam): Promise<FetchResponse<200, types.GetDefiTxsPairResponse200>> {
    return this.core.fetch('/defi/txs/pair', 'get', metadata);
  }

  /**
   * Get list of trades of a token with time bound option.
   *
   * @summary Trades - Token Seek By Time
   * @throws FetchError<400, types.GetDefiTxsTokenSeekByTimeResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTxsTokenSeekByTimeResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTxsTokenSeekByTimeResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTxsTokenSeekByTimeResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTxsTokenSeekByTimeResponse500> Internal Server Error
   */
  getDefiTxsTokenSeek_by_time(metadata: types.GetDefiTxsTokenSeekByTimeMetadataParam): Promise<FetchResponse<200, types.GetDefiTxsTokenSeekByTimeResponse200>> {
    return this.core.fetch('/defi/txs/token/seek_by_time', 'get', metadata);
  }

  /**
   * Get list of trades of a certain pair or market with time bound option.
   *
   * @summary Trades - Pair Seek By Time
   * @throws FetchError<400, types.GetDefiTxsPairSeekByTimeResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTxsPairSeekByTimeResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTxsPairSeekByTimeResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTxsPairSeekByTimeResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTxsPairSeekByTimeResponse500> Internal Server Error
   */
  getDefiTxsPairSeek_by_time(metadata: types.GetDefiTxsPairSeekByTimeMetadataParam): Promise<FetchResponse<200, types.GetDefiTxsPairSeekByTimeResponse200>> {
    return this.core.fetch('/defi/txs/pair/seek_by_time', 'get', metadata);
  }

  /**
   * Get OHLCV price of a token.
   *
   * @summary OHLCV
   * @throws FetchError<400, types.GetDefiOhlcvResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiOhlcvResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiOhlcvResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiOhlcvResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiOhlcvResponse500> Internal Server Error
   */
  getDefiOhlcv(metadata: types.GetDefiOhlcvMetadataParam): Promise<FetchResponse<200, types.GetDefiOhlcvResponse200>> {
    return this.core.fetch('/defi/ohlcv', 'get', metadata);
  }

  /**
   * Get OHLCV price of a pair.
   *
   * @summary OHLCV - Pair
   * @throws FetchError<400, types.GetDefiOhlcvPairResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiOhlcvPairResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiOhlcvPairResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiOhlcvPairResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiOhlcvPairResponse500> Internal Server Error
   */
  getDefiOhlcvPair(metadata: types.GetDefiOhlcvPairMetadataParam): Promise<FetchResponse<200, types.GetDefiOhlcvPairResponse200>> {
    return this.core.fetch('/defi/ohlcv/pair', 'get', metadata);
  }

  /**
   * Get OHLCV price of a base-quote pair.
   *
   * @summary OHLCV - Base/Quote
   * @throws FetchError<400, types.GetDefiOhlcvBaseQuoteResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiOhlcvBaseQuoteResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiOhlcvBaseQuoteResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiOhlcvBaseQuoteResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiOhlcvBaseQuoteResponse500> Internal Server Error
   */
  getDefiOhlcvBase_quote(metadata: types.GetDefiOhlcvBaseQuoteMetadataParam): Promise<FetchResponse<200, types.GetDefiOhlcvBaseQuoteResponse200>> {
    return this.core.fetch('/defi/ohlcv/base_quote', 'get', metadata);
  }

  /**
   * Get token list of any supported chains.
   *
   * @summary Token - List (V1)
   * @throws FetchError<400, types.GetDefiTokenlistResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTokenlistResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTokenlistResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTokenlistResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTokenlistResponse500> Internal Server Error
   */
  getDefiTokenlist(metadata: types.GetDefiTokenlistMetadataParam): Promise<FetchResponse<200, types.GetDefiTokenlistResponse200>> {
    return this.core.fetch('/defi/tokenlist', 'get', metadata);
  }

  /**
   * Get token security of any supported chains.
   *
   * @summary Token - Security
   * @throws FetchError<400, types.GetDefiTokenSecurityResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTokenSecurityResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTokenSecurityResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTokenSecurityResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTokenSecurityResponse500> Internal Server Error
   */
  getDefiToken_security(metadata: types.GetDefiTokenSecurityMetadataParam): Promise<FetchResponse<200, types.GetDefiTokenSecurityResponse200>> {
    return this.core.fetch('/defi/token_security', 'get', metadata);
  }

  /**
   * Get overview of a token.
   *
   * @summary Token - Overview
   * @throws FetchError<400, types.GetDefiTokenOverviewResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTokenOverviewResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTokenOverviewResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTokenOverviewResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTokenOverviewResponse500> Internal Server Error
   */
  getDefiToken_overview(metadata: types.GetDefiTokenOverviewMetadataParam): Promise<FetchResponse<200, types.GetDefiTokenOverviewResponse200>> {
    return this.core.fetch('/defi/token_overview', 'get', metadata);
  }

  /**
   * Get creation info of token
   *
   * @summary Token - Creation Token Info
   * @throws FetchError<400, types.GetDefiTokenCreationInfoResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTokenCreationInfoResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTokenCreationInfoResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTokenCreationInfoResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTokenCreationInfoResponse500> Internal Server Error
   */
  getDefiToken_creation_info(metadata: types.GetDefiTokenCreationInfoMetadataParam): Promise<FetchResponse<200, types.GetDefiTokenCreationInfoResponse200>> {
    return this.core.fetch('/defi/token_creation_info', 'get', metadata);
  }

  /**
   * Get price and volume updates of a token
   *
   * @summary Price Volume - Single
   * @throws FetchError<400, types.GetDefiPriceVolumeSingleResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiPriceVolumeSingleResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiPriceVolumeSingleResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiPriceVolumeSingleResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiPriceVolumeSingleResponse500> Internal Server Error
   */
  getDefiPrice_volumeSingle(metadata: types.GetDefiPriceVolumeSingleMetadataParam): Promise<FetchResponse<200, types.GetDefiPriceVolumeSingleResponse200>> {
    return this.core.fetch('/defi/price_volume/single', 'get', metadata);
  }

  /**
   * Get price and volume updates of maximum 50 tokens
   *
   * @summary Price Volume - Multi
   * @throws FetchError<400, types.PostDefiPriceVolumeMultiResponse400> Bad Request
   * @throws FetchError<401, types.PostDefiPriceVolumeMultiResponse401> Unauthorized
   * @throws FetchError<403, types.PostDefiPriceVolumeMultiResponse403> Forbidden
   * @throws FetchError<429, types.PostDefiPriceVolumeMultiResponse429> Too Many Requests
   * @throws FetchError<500, types.PostDefiPriceVolumeMultiResponse500> Internal Server Error
   */
  postDefiPrice_volumeMulti(body: types.PostDefiPriceVolumeMultiBodyParam, metadata?: types.PostDefiPriceVolumeMultiMetadataParam): Promise<FetchResponse<200, types.PostDefiPriceVolumeMultiResponse200>> {
    return this.core.fetch('/defi/price_volume/multi', 'post', body, metadata);
  }

  /**
   * Retrieve a dynamic and up-to-date list of trending tokens based on specified sorting
   * criteria.
   *
   * @summary Token - Trending List
   * @throws FetchError<400, types.GetDefiTokenTrendingResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiTokenTrendingResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiTokenTrendingResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiTokenTrendingResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiTokenTrendingResponse500> Internal Server Error
   */
  getDefiToken_trending(metadata: types.GetDefiTokenTrendingMetadataParam): Promise<FetchResponse<200, types.GetDefiTokenTrendingResponse200>> {
    return this.core.fetch('/defi/token_trending', 'get', metadata);
  }

  /**
   * This endpoint facilitates the retrieval of a list of tokens on a specified blockchain
   * network. This upgraded version is exclusive to business and enterprise packages. By
   * simply including the header for the requested blockchain without any query parameters,
   * business and enterprise users can get the full list of tokens on the specified
   * blockchain in the URL returned in the response. This removes the need for the limit
   * response of the previous version and reduces the workload of making multiple calls.
   *
   * @summary Token - List all (V2)
   * @throws FetchError<400, types.PostDefiV2TokensAllResponse400> Bad Request
   * @throws FetchError<401, types.PostDefiV2TokensAllResponse401> Unauthorized
   * @throws FetchError<403, types.PostDefiV2TokensAllResponse403> Forbidden
   * @throws FetchError<429, types.PostDefiV2TokensAllResponse429> Too Many Requests
   * @throws FetchError<500, types.PostDefiV2TokensAllResponse500> Internal Server Error
   */
  postDefiV2TokensAll(metadata?: types.PostDefiV2TokensAllMetadataParam): Promise<FetchResponse<200, types.PostDefiV2TokensAllResponse200>> {
    return this.core.fetch('/defi/v2/tokens/all', 'post', metadata);
  }

  /**
   * Get newly listed tokens of any supported chains.
   *
   * @summary Token - New listing
   * @throws FetchError<400, types.GetDefiV2TokensNewListingResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV2TokensNewListingResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV2TokensNewListingResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV2TokensNewListingResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV2TokensNewListingResponse500> Internal Server Error
   */
  getDefiV2TokensNew_listing(metadata: types.GetDefiV2TokensNewListingMetadataParam): Promise<FetchResponse<200, types.GetDefiV2TokensNewListingResponse200>> {
    return this.core.fetch('/defi/v2/tokens/new_listing', 'get', metadata);
  }

  /**
   * Get top traders of given token.
   *
   * @summary Token - Top traders
   * @throws FetchError<400, types.GetDefiV2TokensTopTradersResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV2TokensTopTradersResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV2TokensTopTradersResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV2TokensTopTradersResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV2TokensTopTradersResponse500> Internal Server Error
   */
  getDefiV2TokensTop_traders(metadata: types.GetDefiV2TokensTopTradersMetadataParam): Promise<FetchResponse<200, types.GetDefiV2TokensTopTradersResponse200>> {
    return this.core.fetch('/defi/v2/tokens/top_traders', 'get', metadata);
  }

  /**
   * The API provides detailed information about the markets for a specific cryptocurrency
   * token on a specified blockchain. Users can retrieve data for one or multiple markets
   * related to a single token. This endpoint requires the specification of a token address
   * and the blockchain to filter results. Additionally, it supports optional query
   * parameters such as offset, limit, and required sorting by liquidity or sort type
   * (ascending or descending) to refine the output.
   *
   * @summary Token - All Market List
   * @throws FetchError<400, types.GetDefiV2MarketsResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV2MarketsResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV2MarketsResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV2MarketsResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV2MarketsResponse500> Internal Server Error
   */
  getDefiV2Markets(metadata: types.GetDefiV2MarketsMetadataParam): Promise<FetchResponse<200, types.GetDefiV2MarketsResponse200>> {
    return this.core.fetch('/defi/v2/markets', 'get', metadata);
  }

  /**
   * Get metadata of single token
   *
   * @summary Token - Metadata (Single)
   * @throws FetchError<400, types.GetDefiV3TokenMetaDataSingleResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3TokenMetaDataSingleResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3TokenMetaDataSingleResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3TokenMetaDataSingleResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3TokenMetaDataSingleResponse500> Internal Server Error
   */
  getDefiV3TokenMetaDataSingle(metadata: types.GetDefiV3TokenMetaDataSingleMetadataParam): Promise<FetchResponse<200, types.GetDefiV3TokenMetaDataSingleResponse200>> {
    return this.core.fetch('/defi/v3/token/meta-data/single', 'get', metadata);
  }

  /**
   * Get metadata of multiple tokens
   *
   * @summary Token - Metadata (Multiple)
   * @throws FetchError<400, types.GetDefiV3TokenMetaDataMultipleResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3TokenMetaDataMultipleResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3TokenMetaDataMultipleResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3TokenMetaDataMultipleResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3TokenMetaDataMultipleResponse500> Internal Server Error
   */
  getDefiV3TokenMetaDataMultiple(metadata: types.GetDefiV3TokenMetaDataMultipleMetadataParam): Promise<FetchResponse<200, types.GetDefiV3TokenMetaDataMultipleResponse200>> {
    return this.core.fetch('/defi/v3/token/meta-data/multiple', 'get', metadata);
  }

  /**
   * Get overview of multiple pairs
   *
   * @summary Pair - Pair Overview (Multiple)
   * @throws FetchError<400, types.GetDefiV3PairOverviewMultipleResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3PairOverviewMultipleResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3PairOverviewMultipleResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3PairOverviewMultipleResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3PairOverviewMultipleResponse500> Internal Server Error
   */
  getDefiV3PairOverviewMultiple(metadata: types.GetDefiV3PairOverviewMultipleMetadataParam): Promise<FetchResponse<200, types.GetDefiV3PairOverviewMultipleResponse200>> {
    return this.core.fetch('/defi/v3/pair/overview/multiple', 'get', metadata);
  }

  /**
   * Get overview of single pair
   *
   * @summary Pair - Pair Overview (Single)
   * @throws FetchError<400, types.GetDefiV3PairOverviewSingleResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3PairOverviewSingleResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3PairOverviewSingleResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3PairOverviewSingleResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3PairOverviewSingleResponse500> Internal Server Error
   */
  getDefiV3PairOverviewSingle(metadata: types.GetDefiV3PairOverviewSingleMetadataParam): Promise<FetchResponse<200, types.GetDefiV3PairOverviewSingleResponse200>> {
    return this.core.fetch('/defi/v3/pair/overview/single', 'get', metadata);
  }

  /**
   * Get market data of single token
   *
   * @summary Token - Market Data
   * @throws FetchError<400, types.GetDefiV3TokenMarketDataResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3TokenMarketDataResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3TokenMarketDataResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3TokenMarketDataResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3TokenMarketDataResponse500> Internal Server Error
   */
  getDefiV3TokenMarketData(metadata: types.GetDefiV3TokenMarketDataMetadataParam): Promise<FetchResponse<200, types.GetDefiV3TokenMarketDataResponse200>> {
    return this.core.fetch('/defi/v3/token/market-data', 'get', metadata);
  }

  /**
   * Get trade data of single token
   *
   * @summary Token - Trade Data (Single)
   * @throws FetchError<400, types.GetDefiV3TokenTradeDataSingleResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3TokenTradeDataSingleResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3TokenTradeDataSingleResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3TokenTradeDataSingleResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3TokenTradeDataSingleResponse500> Internal Server Error
   */
  getDefiV3TokenTradeDataSingle(metadata: types.GetDefiV3TokenTradeDataSingleMetadataParam): Promise<FetchResponse<200, types.GetDefiV3TokenTradeDataSingleResponse200>> {
    return this.core.fetch('/defi/v3/token/trade-data/single', 'get', metadata);
  }

  /**
   * Get trade data of multiple tokens
   *
   * @summary Token - Trade Data (Multiple)
   * @throws FetchError<400, types.GetDefiV3TokenTradeDataMultipleResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3TokenTradeDataMultipleResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3TokenTradeDataMultipleResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3TokenTradeDataMultipleResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3TokenTradeDataMultipleResponse500> Internal Server Error
   */
  getDefiV3TokenTradeDataMultiple(metadata: types.GetDefiV3TokenTradeDataMultipleMetadataParam): Promise<FetchResponse<200, types.GetDefiV3TokenTradeDataMultipleResponse200>> {
    return this.core.fetch('/defi/v3/token/trade-data/multiple', 'get', metadata);
  }

  /**
   * Get top holder list of the given token
   *
   * @summary Token - Holder
   * @throws FetchError<400, types.GetDefiV3TokenHolderResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3TokenHolderResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3TokenHolderResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3TokenHolderResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3TokenHolderResponse500> Internal Server Error
   */
  getDefiV3TokenHolder(metadata: types.GetDefiV3TokenHolderMetadataParam): Promise<FetchResponse<200, types.GetDefiV3TokenHolderResponse200>> {
    return this.core.fetch('/defi/v3/token/holder', 'get', metadata);
  }

  /**
   * Search for token and market data by matching a pattern or a specific token, market
   * address.
   *
   * @summary Search - Token, market Data
   * @throws FetchError<400, types.GetDefiV3SearchResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3SearchResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3SearchResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3SearchResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3SearchResponse500> Internal Server Error
   */
  getDefiV3Search(metadata: types.GetDefiV3SearchMetadataParam): Promise<FetchResponse<200, types.GetDefiV3SearchResponse200>> {
    return this.core.fetch('/defi/v3/search', 'get', metadata);
  }

  /**
   * Get mint/burn transaction list of the given token. Only support solana currently
   *
   * @summary Token - Mint/Burn
   * @throws FetchError<400, types.GetDefiV3TokenMintBurnTxsResponse400> Bad Request
   * @throws FetchError<401, types.GetDefiV3TokenMintBurnTxsResponse401> Unauthorized
   * @throws FetchError<403, types.GetDefiV3TokenMintBurnTxsResponse403> Forbidden
   * @throws FetchError<429, types.GetDefiV3TokenMintBurnTxsResponse429> Too Many Requests
   * @throws FetchError<500, types.GetDefiV3TokenMintBurnTxsResponse500> Internal Server Error
   */
  getDefiV3TokenMintBurnTxs(metadata: types.GetDefiV3TokenMintBurnTxsMetadataParam): Promise<FetchResponse<200, types.GetDefiV3TokenMintBurnTxsResponse200>> {
    return this.core.fetch('/defi/v3/token/mint-burn-txs', 'get', metadata);
  }

  /**
   * Supported Networks
   *
   * @throws FetchError<400, types.GetV1WalletListSupportedChainResponse400> Bad Request
   * @throws FetchError<401, types.GetV1WalletListSupportedChainResponse401> Unauthorized
   * @throws FetchError<403, types.GetV1WalletListSupportedChainResponse403> Forbidden
   * @throws FetchError<429, types.GetV1WalletListSupportedChainResponse429> Too Many Requests
   * @throws FetchError<500, types.GetV1WalletListSupportedChainResponse500> Internal Server Error
   */
  getV1WalletList_supported_chain(): Promise<FetchResponse<200, types.GetV1WalletListSupportedChainResponse200>> {
    return this.core.fetch('/v1/wallet/list_supported_chain', 'get');
  }

  /**
   * Wallet Portfolio
   *
   * @throws FetchError<400, types.GetV1WalletTokenListResponse400> Bad Request
   * @throws FetchError<401, types.GetV1WalletTokenListResponse401> Unauthorized
   * @throws FetchError<403, types.GetV1WalletTokenListResponse403> Forbidden
   * @throws FetchError<429, types.GetV1WalletTokenListResponse429> Too Many Requests
   * @throws FetchError<500, types.GetV1WalletTokenListResponse500> Internal Server Error
   */
  getV1WalletToken_list(metadata: types.GetV1WalletTokenListMetadataParam): Promise<FetchResponse<200, types.GetV1WalletTokenListResponse200>> {
    return this.core.fetch('/v1/wallet/token_list', 'get', metadata);
  }

  /**
   * Wallet Portfolio - Multichain
   *
   * @throws FetchError<400, types.GetV1WalletMultichainTokenListResponse400> Bad Request
   * @throws FetchError<401, types.GetV1WalletMultichainTokenListResponse401> Unauthorized
   * @throws FetchError<403, types.GetV1WalletMultichainTokenListResponse403> Forbidden
   * @throws FetchError<429, types.GetV1WalletMultichainTokenListResponse429> Too Many Requests
   * @throws FetchError<500, types.GetV1WalletMultichainTokenListResponse500> Internal Server Error
   */
  getV1WalletMultichain_token_list(metadata: types.GetV1WalletMultichainTokenListMetadataParam): Promise<FetchResponse<200, types.GetV1WalletMultichainTokenListResponse200>> {
    return this.core.fetch('/v1/wallet/multichain_token_list', 'get', metadata);
  }

  /**
   * Wallet - Token Balance
   *
   * @throws FetchError<400, types.GetV1WalletTokenBalanceResponse400> Bad Request
   * @throws FetchError<401, types.GetV1WalletTokenBalanceResponse401> Unauthorized
   * @throws FetchError<403, types.GetV1WalletTokenBalanceResponse403> Forbidden
   * @throws FetchError<429, types.GetV1WalletTokenBalanceResponse429> Too Many Requests
   * @throws FetchError<500, types.GetV1WalletTokenBalanceResponse500> Internal Server Error
   */
  getV1WalletToken_balance(metadata: types.GetV1WalletTokenBalanceMetadataParam): Promise<FetchResponse<200, types.GetV1WalletTokenBalanceResponse200>> {
    return this.core.fetch('/v1/wallet/token_balance', 'get', metadata);
  }

  /**
   * Wallet Transaction History
   *
   * @throws FetchError<400, types.GetV1WalletTxListResponse400> Bad Request
   * @throws FetchError<401, types.GetV1WalletTxListResponse401> Unauthorized
   * @throws FetchError<403, types.GetV1WalletTxListResponse403> Forbidden
   * @throws FetchError<429, types.GetV1WalletTxListResponse429> Too Many Requests
   * @throws FetchError<500, types.GetV1WalletTxListResponse500> Internal Server Error
   */
  getV1WalletTx_list(metadata: types.GetV1WalletTxListMetadataParam): Promise<FetchResponse<200, types.GetV1WalletTxListResponse200>> {
    return this.core.fetch('/v1/wallet/tx_list', 'get', metadata);
  }

  /**
   * Wallet Transaction History - Multichain
   *
   * @throws FetchError<400, types.GetV1WalletMultichainTxListResponse400> Bad Request
   * @throws FetchError<401, types.GetV1WalletMultichainTxListResponse401> Unauthorized
   * @throws FetchError<403, types.GetV1WalletMultichainTxListResponse403> Forbidden
   * @throws FetchError<429, types.GetV1WalletMultichainTxListResponse429> Too Many Requests
   * @throws FetchError<500, types.GetV1WalletMultichainTxListResponse500> Internal Server Error
   */
  getV1WalletMultichain_tx_list(metadata: types.GetV1WalletMultichainTxListMetadataParam): Promise<FetchResponse<200, types.GetV1WalletMultichainTxListResponse200>> {
    return this.core.fetch('/v1/wallet/multichain_tx_list', 'get', metadata);
  }

  /**
   * Transaction Simulation
   *
   * @throws FetchError<400, types.PostV1WalletSimulateResponse400> Bad Request
   * @throws FetchError<401, types.PostV1WalletSimulateResponse401> Unauthorized
   * @throws FetchError<403, types.PostV1WalletSimulateResponse403> Forbidden
   * @throws FetchError<429, types.PostV1WalletSimulateResponse429> Too Many Requests
   * @throws FetchError<500, types.PostV1WalletSimulateResponse500> Internal Server Error
   */
  postV1WalletSimulate(body: types.PostV1WalletSimulateBodyParam, metadata: types.PostV1WalletSimulateMetadataParam): Promise<FetchResponse<200, types.PostV1WalletSimulateResponse200>> {
    return this.core.fetch('/v1/wallet/simulate', 'post', body, metadata);
  }

  /**
   * The API provides detailed information top gainers/losers
   *
   * @summary Trader - Gainers/Losers
   * @throws FetchError<400, types.GetTraderGainersLosersResponse400> Bad Request
   * @throws FetchError<401, types.GetTraderGainersLosersResponse401> Unauthorized
   * @throws FetchError<403, types.GetTraderGainersLosersResponse403> Forbidden
   * @throws FetchError<429, types.GetTraderGainersLosersResponse429> Too Many Requests
   * @throws FetchError<500, types.GetTraderGainersLosersResponse500> Internal Server Error
   */
  getTraderGainersLosers(metadata: types.GetTraderGainersLosersMetadataParam): Promise<FetchResponse<200, types.GetTraderGainersLosersResponse200>> {
    return this.core.fetch('/trader/gainers-losers', 'get', metadata);
  }

  /**
   * Get list of trades of a trader with time bound option.
   *
   * @summary Trader - Trades Seek By Time
   * @throws FetchError<400, types.GetTraderTxsSeekByTimeResponse400> Bad Request
   * @throws FetchError<401, types.GetTraderTxsSeekByTimeResponse401> Unauthorized
   * @throws FetchError<403, types.GetTraderTxsSeekByTimeResponse403> Forbidden
   * @throws FetchError<429, types.GetTraderTxsSeekByTimeResponse429> Too Many Requests
   * @throws FetchError<500, types.GetTraderTxsSeekByTimeResponse500> Internal Server Error
   */
  getTraderTxsSeek_by_time(metadata: types.GetTraderTxsSeekByTimeMetadataParam): Promise<FetchResponse<200, types.GetTraderTxsSeekByTimeResponse200>> {
    return this.core.fetch('/trader/txs/seek_by_time', 'get', metadata);
  }
}

const createSDK = (() => { return new SDK(); })()
;

export default createSDK;

export type { GetDefiHistoricalPriceUnixMetadataParam, GetDefiHistoricalPriceUnixResponse200, GetDefiHistoricalPriceUnixResponse400, GetDefiHistoricalPriceUnixResponse401, GetDefiHistoricalPriceUnixResponse403, GetDefiHistoricalPriceUnixResponse429, GetDefiHistoricalPriceUnixResponse500, GetDefiHistoryPriceMetadataParam, GetDefiHistoryPriceResponse200, GetDefiHistoryPriceResponse400, GetDefiHistoryPriceResponse401, GetDefiHistoryPriceResponse403, GetDefiHistoryPriceResponse429, GetDefiHistoryPriceResponse500, GetDefiMultiPriceMetadataParam, GetDefiMultiPriceResponse200, GetDefiMultiPriceResponse400, GetDefiMultiPriceResponse401, GetDefiMultiPriceResponse403, GetDefiMultiPriceResponse429, GetDefiMultiPriceResponse500, GetDefiNetworksResponse200, GetDefiNetworksResponse400, GetDefiNetworksResponse401, GetDefiNetworksResponse403, GetDefiNetworksResponse429, GetDefiNetworksResponse500, GetDefiOhlcvBaseQuoteMetadataParam, GetDefiOhlcvBaseQuoteResponse200, GetDefiOhlcvBaseQuoteResponse400, GetDefiOhlcvBaseQuoteResponse401, GetDefiOhlcvBaseQuoteResponse403, GetDefiOhlcvBaseQuoteResponse429, GetDefiOhlcvBaseQuoteResponse500, GetDefiOhlcvMetadataParam, GetDefiOhlcvPairMetadataParam, GetDefiOhlcvPairResponse200, GetDefiOhlcvPairResponse400, GetDefiOhlcvPairResponse401, GetDefiOhlcvPairResponse403, GetDefiOhlcvPairResponse429, GetDefiOhlcvPairResponse500, GetDefiOhlcvResponse200, GetDefiOhlcvResponse400, GetDefiOhlcvResponse401, GetDefiOhlcvResponse403, GetDefiOhlcvResponse429, GetDefiOhlcvResponse500, GetDefiPriceMetadataParam, GetDefiPriceResponse200, GetDefiPriceResponse400, GetDefiPriceResponse401, GetDefiPriceResponse403, GetDefiPriceResponse429, GetDefiPriceResponse500, GetDefiPriceVolumeSingleMetadataParam, GetDefiPriceVolumeSingleResponse200, GetDefiPriceVolumeSingleResponse400, GetDefiPriceVolumeSingleResponse401, GetDefiPriceVolumeSingleResponse403, GetDefiPriceVolumeSingleResponse429, GetDefiPriceVolumeSingleResponse500, GetDefiTokenCreationInfoMetadataParam, GetDefiTokenCreationInfoResponse200, GetDefiTokenCreationInfoResponse400, GetDefiTokenCreationInfoResponse401, GetDefiTokenCreationInfoResponse403, GetDefiTokenCreationInfoResponse429, GetDefiTokenCreationInfoResponse500, GetDefiTokenOverviewMetadataParam, GetDefiTokenOverviewResponse200, GetDefiTokenOverviewResponse400, GetDefiTokenOverviewResponse401, GetDefiTokenOverviewResponse403, GetDefiTokenOverviewResponse429, GetDefiTokenOverviewResponse500, GetDefiTokenSecurityMetadataParam, GetDefiTokenSecurityResponse200, GetDefiTokenSecurityResponse400, GetDefiTokenSecurityResponse401, GetDefiTokenSecurityResponse403, GetDefiTokenSecurityResponse429, GetDefiTokenSecurityResponse500, GetDefiTokenTrendingMetadataParam, GetDefiTokenTrendingResponse200, GetDefiTokenTrendingResponse400, GetDefiTokenTrendingResponse401, GetDefiTokenTrendingResponse403, GetDefiTokenTrendingResponse429, GetDefiTokenTrendingResponse500, GetDefiTokenlistMetadataParam, GetDefiTokenlistResponse200, GetDefiTokenlistResponse400, GetDefiTokenlistResponse401, GetDefiTokenlistResponse403, GetDefiTokenlistResponse429, GetDefiTokenlistResponse500, GetDefiTxsPairMetadataParam, GetDefiTxsPairResponse200, GetDefiTxsPairResponse400, GetDefiTxsPairResponse401, GetDefiTxsPairResponse403, GetDefiTxsPairResponse429, GetDefiTxsPairResponse500, GetDefiTxsPairSeekByTimeMetadataParam, GetDefiTxsPairSeekByTimeResponse200, GetDefiTxsPairSeekByTimeResponse400, GetDefiTxsPairSeekByTimeResponse401, GetDefiTxsPairSeekByTimeResponse403, GetDefiTxsPairSeekByTimeResponse429, GetDefiTxsPairSeekByTimeResponse500, GetDefiTxsTokenMetadataParam, GetDefiTxsTokenResponse200, GetDefiTxsTokenResponse400, GetDefiTxsTokenResponse401, GetDefiTxsTokenResponse403, GetDefiTxsTokenResponse429, GetDefiTxsTokenResponse500, GetDefiTxsTokenSeekByTimeMetadataParam, GetDefiTxsTokenSeekByTimeResponse200, GetDefiTxsTokenSeekByTimeResponse400, GetDefiTxsTokenSeekByTimeResponse401, GetDefiTxsTokenSeekByTimeResponse403, GetDefiTxsTokenSeekByTimeResponse429, GetDefiTxsTokenSeekByTimeResponse500, GetDefiV2MarketsMetadataParam, GetDefiV2MarketsResponse200, GetDefiV2MarketsResponse400, GetDefiV2MarketsResponse401, GetDefiV2MarketsResponse403, GetDefiV2MarketsResponse429, GetDefiV2MarketsResponse500, GetDefiV2TokensNewListingMetadataParam, GetDefiV2TokensNewListingResponse200, GetDefiV2TokensNewListingResponse400, GetDefiV2TokensNewListingResponse401, GetDefiV2TokensNewListingResponse403, GetDefiV2TokensNewListingResponse429, GetDefiV2TokensNewListingResponse500, GetDefiV2TokensTopTradersMetadataParam, GetDefiV2TokensTopTradersResponse200, GetDefiV2TokensTopTradersResponse400, GetDefiV2TokensTopTradersResponse401, GetDefiV2TokensTopTradersResponse403, GetDefiV2TokensTopTradersResponse429, GetDefiV2TokensTopTradersResponse500, GetDefiV3PairOverviewMultipleMetadataParam, GetDefiV3PairOverviewMultipleResponse200, GetDefiV3PairOverviewMultipleResponse400, GetDefiV3PairOverviewMultipleResponse401, GetDefiV3PairOverviewMultipleResponse403, GetDefiV3PairOverviewMultipleResponse429, GetDefiV3PairOverviewMultipleResponse500, GetDefiV3PairOverviewSingleMetadataParam, GetDefiV3PairOverviewSingleResponse200, GetDefiV3PairOverviewSingleResponse400, GetDefiV3PairOverviewSingleResponse401, GetDefiV3PairOverviewSingleResponse403, GetDefiV3PairOverviewSingleResponse429, GetDefiV3PairOverviewSingleResponse500, GetDefiV3SearchMetadataParam, GetDefiV3SearchResponse200, GetDefiV3SearchResponse400, GetDefiV3SearchResponse401, GetDefiV3SearchResponse403, GetDefiV3SearchResponse429, GetDefiV3SearchResponse500, GetDefiV3TokenHolderMetadataParam, GetDefiV3TokenHolderResponse200, GetDefiV3TokenHolderResponse400, GetDefiV3TokenHolderResponse401, GetDefiV3TokenHolderResponse403, GetDefiV3TokenHolderResponse429, GetDefiV3TokenHolderResponse500, GetDefiV3TokenMarketDataMetadataParam, GetDefiV3TokenMarketDataResponse200, GetDefiV3TokenMarketDataResponse400, GetDefiV3TokenMarketDataResponse401, GetDefiV3TokenMarketDataResponse403, GetDefiV3TokenMarketDataResponse429, GetDefiV3TokenMarketDataResponse500, GetDefiV3TokenMetaDataMultipleMetadataParam, GetDefiV3TokenMetaDataMultipleResponse200, GetDefiV3TokenMetaDataMultipleResponse400, GetDefiV3TokenMetaDataMultipleResponse401, GetDefiV3TokenMetaDataMultipleResponse403, GetDefiV3TokenMetaDataMultipleResponse429, GetDefiV3TokenMetaDataMultipleResponse500, GetDefiV3TokenMetaDataSingleMetadataParam, GetDefiV3TokenMetaDataSingleResponse200, GetDefiV3TokenMetaDataSingleResponse400, GetDefiV3TokenMetaDataSingleResponse401, GetDefiV3TokenMetaDataSingleResponse403, GetDefiV3TokenMetaDataSingleResponse429, GetDefiV3TokenMetaDataSingleResponse500, GetDefiV3TokenMintBurnTxsMetadataParam, GetDefiV3TokenMintBurnTxsResponse200, GetDefiV3TokenMintBurnTxsResponse400, GetDefiV3TokenMintBurnTxsResponse401, GetDefiV3TokenMintBurnTxsResponse403, GetDefiV3TokenMintBurnTxsResponse429, GetDefiV3TokenMintBurnTxsResponse500, GetDefiV3TokenTradeDataMultipleMetadataParam, GetDefiV3TokenTradeDataMultipleResponse200, GetDefiV3TokenTradeDataMultipleResponse400, GetDefiV3TokenTradeDataMultipleResponse401, GetDefiV3TokenTradeDataMultipleResponse403, GetDefiV3TokenTradeDataMultipleResponse429, GetDefiV3TokenTradeDataMultipleResponse500, GetDefiV3TokenTradeDataSingleMetadataParam, GetDefiV3TokenTradeDataSingleResponse200, GetDefiV3TokenTradeDataSingleResponse400, GetDefiV3TokenTradeDataSingleResponse401, GetDefiV3TokenTradeDataSingleResponse403, GetDefiV3TokenTradeDataSingleResponse429, GetDefiV3TokenTradeDataSingleResponse500, GetTraderGainersLosersMetadataParam, GetTraderGainersLosersResponse200, GetTraderGainersLosersResponse400, GetTraderGainersLosersResponse401, GetTraderGainersLosersResponse403, GetTraderGainersLosersResponse429, GetTraderGainersLosersResponse500, GetTraderTxsSeekByTimeMetadataParam, GetTraderTxsSeekByTimeResponse200, GetTraderTxsSeekByTimeResponse400, GetTraderTxsSeekByTimeResponse401, GetTraderTxsSeekByTimeResponse403, GetTraderTxsSeekByTimeResponse429, GetTraderTxsSeekByTimeResponse500, GetV1WalletListSupportedChainResponse200, GetV1WalletListSupportedChainResponse400, GetV1WalletListSupportedChainResponse401, GetV1WalletListSupportedChainResponse403, GetV1WalletListSupportedChainResponse429, GetV1WalletListSupportedChainResponse500, GetV1WalletMultichainTokenListMetadataParam, GetV1WalletMultichainTokenListResponse200, GetV1WalletMultichainTokenListResponse400, GetV1WalletMultichainTokenListResponse401, GetV1WalletMultichainTokenListResponse403, GetV1WalletMultichainTokenListResponse429, GetV1WalletMultichainTokenListResponse500, GetV1WalletMultichainTxListMetadataParam, GetV1WalletMultichainTxListResponse200, GetV1WalletMultichainTxListResponse400, GetV1WalletMultichainTxListResponse401, GetV1WalletMultichainTxListResponse403, GetV1WalletMultichainTxListResponse429, GetV1WalletMultichainTxListResponse500, GetV1WalletTokenBalanceMetadataParam, GetV1WalletTokenBalanceResponse200, GetV1WalletTokenBalanceResponse400, GetV1WalletTokenBalanceResponse401, GetV1WalletTokenBalanceResponse403, GetV1WalletTokenBalanceResponse429, GetV1WalletTokenBalanceResponse500, GetV1WalletTokenListMetadataParam, GetV1WalletTokenListResponse200, GetV1WalletTokenListResponse400, GetV1WalletTokenListResponse401, GetV1WalletTokenListResponse403, GetV1WalletTokenListResponse429, GetV1WalletTokenListResponse500, GetV1WalletTxListMetadataParam, GetV1WalletTxListResponse200, GetV1WalletTxListResponse400, GetV1WalletTxListResponse401, GetV1WalletTxListResponse403, GetV1WalletTxListResponse429, GetV1WalletTxListResponse500, PostDefiMultiPriceBodyParam, PostDefiMultiPriceMetadataParam, PostDefiMultiPriceResponse200, PostDefiMultiPriceResponse400, PostDefiMultiPriceResponse401, PostDefiMultiPriceResponse403, PostDefiMultiPriceResponse429, PostDefiMultiPriceResponse500, PostDefiPriceVolumeMultiBodyParam, PostDefiPriceVolumeMultiMetadataParam, PostDefiPriceVolumeMultiResponse200, PostDefiPriceVolumeMultiResponse400, PostDefiPriceVolumeMultiResponse401, PostDefiPriceVolumeMultiResponse403, PostDefiPriceVolumeMultiResponse429, PostDefiPriceVolumeMultiResponse500, PostDefiV2TokensAllMetadataParam, PostDefiV2TokensAllResponse200, PostDefiV2TokensAllResponse400, PostDefiV2TokensAllResponse401, PostDefiV2TokensAllResponse403, PostDefiV2TokensAllResponse429, PostDefiV2TokensAllResponse500, PostV1WalletSimulateBodyParam, PostV1WalletSimulateMetadataParam, PostV1WalletSimulateResponse200, PostV1WalletSimulateResponse400, PostV1WalletSimulateResponse401, PostV1WalletSimulateResponse403, PostV1WalletSimulateResponse429, PostV1WalletSimulateResponse500 } from './types';
