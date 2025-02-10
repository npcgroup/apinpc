"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.HyperLiquidAPI = void 0;
var node_fetch_1 = require("node-fetch");
var HyperLiquidAPI = /** @class */ (function () {
    function HyperLiquidAPI() {
        this.baseUrl = 'https://api.hyperliquid.xyz';
    }
    /**
     * Get predicted funding rates for all assets
     */
    HyperLiquidAPI.prototype.getPredictedFundingRates = function () {
        return __awaiter(this, void 0, void 0, function () {
            var response, errorText, rawData;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, (0, node_fetch_1.default)("".concat(this.baseUrl, "/info"), {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                type: 'predictedFundings'
                            })
                        })];
                    case 1:
                        response = _a.sent();
                        if (!!response.ok) return [3 /*break*/, 3];
                        return [4 /*yield*/, response.text()];
                    case 2:
                        errorText = _a.sent();
                        throw new Error("API Error ".concat(response.status, ": ").concat(errorText));
                    case 3: return [4 /*yield*/, response.json()];
                    case 4:
                        rawData = _a.sent();
                        // Transform the response into a more readable format
                        return [2 /*return*/, rawData
                                .map(function (_a) {
                                var _b;
                                var asset = _a[0], exchangeData = _a[1];
                                // Find HyperLiquid data (marked as "HlPerp" in the response)
                                var hlData = (_b = exchangeData.find(function (_a) {
                                    var exchange = _a[0];
                                    return exchange === 'HlPerp';
                                })) === null || _b === void 0 ? void 0 : _b[1];
                                if (!hlData)
                                    return null;
                                var predicted = parseFloat(hlData.fundingRate);
                                return {
                                    asset: asset,
                                    predicted: isNaN(predicted) ? 0 : predicted,
                                    timestamp: Date.now()
                                };
                            })
                                .filter(function (rate) {
                                return rate !== null &&
                                    !isNaN(rate.predicted) &&
                                    rate.predicted !== 0;
                            })];
                }
            });
        });
    };
    /**
     * Get predicted funding rate for a specific asset
     */
    HyperLiquidAPI.prototype.getPredictedFundingRate = function (asset) {
        return __awaiter(this, void 0, void 0, function () {
            var rates;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, this.getPredictedFundingRates()];
                    case 1:
                        rates = _a.sent();
                        return [2 /*return*/, rates.find(function (rate) { return rate.asset === asset; }) || null];
                }
            });
        });
    };
    /**
     * Analyze funding rates data
     */
    HyperLiquidAPI.prototype.analyzeFundingRates = function (rates, topN) {
        if (topN === void 0) { topN = 5; }
        var validRates = rates.filter(function (rate) { return !isNaN(rate.predicted) && rate.predicted !== 0; });
        var sortedRates = validRates.sort(function (a, b) { return Math.abs(b.predicted) - Math.abs(a.predicted); });
        var positiveRates = validRates.filter(function (r) { return r.predicted > 0; });
        var negativeRates = validRates.filter(function (r) { return r.predicted < 0; });
        var averageRate = validRates.length > 0
            ? validRates.reduce(function (sum, rate) { return sum + rate.predicted; }, 0) / validRates.length
            : 0;
        return {
            topOpportunities: sortedRates.slice(0, topN),
            statistics: {
                totalPairs: rates.length,
                pairsWithFunding: validRates.length,
                positiveRates: positiveRates.length,
                negativeRates: negativeRates.length,
                highestRate: sortedRates[0] || null,
                averageRate: averageRate
            }
        };
    };
    /**
     * Format funding rate for display
     */
    HyperLiquidAPI.prototype.formatFundingRate = function (rate, includeAnnualized) {
        if (includeAnnualized === void 0) { includeAnnualized = true; }
        var fundingPercent = (rate.predicted * 100).toFixed(6);
        var direction = rate.predicted >= 0 ? 'LONGS PAY' : 'SHORTS PAY';
        var annualized = (rate.predicted * 100 * 365).toFixed(2);
        return includeAnnualized
            ? "".concat(rate.asset.padEnd(10), " ").concat(fundingPercent.padStart(10), "% (").concat(annualized, "% APR) - ").concat(direction)
            : "".concat(rate.asset.padEnd(10), " ").concat(fundingPercent.padStart(10), "% (").concat(direction, ")");
    };
    return HyperLiquidAPI;
}());
exports.HyperLiquidAPI = HyperLiquidAPI;
