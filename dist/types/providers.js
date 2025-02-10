"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChainName = exports.Environment = exports.AssetType = exports.DataProvider = void 0;
var DataProvider;
(function (DataProvider) {
    DataProvider["DEFILLAMA"] = "defillama";
    DataProvider["DUNE"] = "dune";
    DataProvider["BITQUERY"] = "bitquery";
    DataProvider["FOOTPRINT"] = "footprint";
    DataProvider["THEGRAPH"] = "thegraph";
    DataProvider["HYPERLIQUID"] = "hyperliquid";
})(DataProvider || (exports.DataProvider = DataProvider = {}));
var AssetType;
(function (AssetType) {
    AssetType["TOKEN"] = "token";
    AssetType["NFT"] = "nft";
    AssetType["PERPETUAL"] = "perpetual";
    AssetType["SYNTHETIC"] = "synthetic";
    AssetType["OPTION"] = "option";
})(AssetType || (exports.AssetType = AssetType = {}));
var Environment;
(function (Environment) {
    Environment["TEST"] = "test";
    Environment["PRODUCTION"] = "production";
})(Environment || (exports.Environment = Environment = {}));
var ChainName;
(function (ChainName) {
    ChainName["ETHEREUM"] = "ethereum";
    ChainName["SOLANA"] = "solana";
    ChainName["ARBITRUM"] = "arbitrum";
    ChainName["OPTIMISM"] = "optimism";
    ChainName["BASE"] = "base";
    ChainName["POLYGON"] = "polygon";
})(ChainName || (exports.ChainName = ChainName = {}));
