"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
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
exports.SupabaseFundingPipeline = void 0;
var funding_pipeline_1 = require("./funding-pipeline");
var supabase_client_1 = require("./utils/supabase-client");
var SupabaseFundingPipeline = /** @class */ (function (_super) {
    __extends(SupabaseFundingPipeline, _super);
    function SupabaseFundingPipeline(options) {
        if (options === void 0) { options = {}; }
        return _super.call(this, options) || this;
    }
    SupabaseFundingPipeline.prototype.insertPredictedRates = function (rates) {
        return __awaiter(this, void 0, void 0, function () {
            var _a, data, error, error_1;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        this.log("Inserting ".concat(rates.length, " predicted rates into Supabase..."), 'verbose');
                        _b.label = 1;
                    case 1:
                        _b.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, supabase_client_1.supabase
                                .from('predicted_funding_rates')
                                .insert(rates)
                                .select()];
                    case 2:
                        _a = _b.sent(), data = _a.data, error = _a.error;
                        if (error) {
                            this.log("Supabase error: ".concat(JSON.stringify(error)), 'minimal');
                            throw new Error("Failed to insert rates: ".concat(error.message));
                        }
                        this.log("Successfully inserted ".concat((data === null || data === void 0 ? void 0 : data.length) || 0, " new rates"), 'normal');
                        return [2 /*return*/, data];
                    case 3:
                        error_1 = _b.sent();
                        this.log("Insert error: ".concat(error_1 instanceof Error ? error_1.message : JSON.stringify(error_1)), 'minimal');
                        throw error_1;
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    SupabaseFundingPipeline.prototype.runOnce = function () {
        return __awaiter(this, void 0, void 0, function () {
            var response, rawData, timestamp, created_at, allRates, validRates, _i, rawData_1, _a, asset, exchanges, _b, exchanges_1, _c, exchangeName, data, rate, nextFundingTime, error_2;
            return __generator(this, function (_d) {
                switch (_d.label) {
                    case 0:
                        _d.trys.push([0, 6, , 7]);
                        return [4 /*yield*/, fetch('https://api.hyperliquid.xyz/info', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ type: 'predictedFundings' })
                            })];
                    case 1:
                        response = _d.sent();
                        if (!response.ok) {
                            throw new Error("API Error ".concat(response.status));
                        }
                        return [4 /*yield*/, response.json()];
                    case 2:
                        rawData = _d.sent();
                        timestamp = new Date().toISOString();
                        created_at = timestamp;
                        allRates = [];
                        validRates = [];
                        for (_i = 0, rawData_1 = rawData; _i < rawData_1.length; _i++) {
                            _a = rawData_1[_i], asset = _a[0], exchanges = _a[1];
                            for (_b = 0, exchanges_1 = exchanges; _b < exchanges_1.length; _b++) {
                                _c = exchanges_1[_b], exchangeName = _c[0], data = _c[1];
                                if (data && data.fundingRate) {
                                    rate = parseFloat(data.fundingRate);
                                    if (!isNaN(rate)) { // Remove zero check to include all valid rates
                                        nextFundingTime = new Date(data.nextFundingTime).toISOString();
                                        allRates.push({
                                            timestamp: timestamp,
                                            asset: asset,
                                            predicted_rate: rate,
                                            annualized_rate: rate * 365,
                                            direction: rate >= 0 ? 'LONGS_PAY' : 'SHORTS_PAY',
                                            exchange: exchangeName,
                                            next_funding_time: nextFundingTime,
                                            created_at: created_at
                                        });
                                        validRates.push({
                                            asset: asset,
                                            predicted: rate,
                                            timestamp: Date.now()
                                        });
                                    }
                                }
                            }
                        }
                        if (!(allRates.length === 0)) return [3 /*break*/, 3];
                        this.log('No valid rates found', 'normal');
                        return [3 /*break*/, 5];
                    case 3:
                        this.log("Found ".concat(allRates.length, " rates across all exchanges"), 'normal');
                        return [4 /*yield*/, this.insertPredictedRates(allRates)];
                    case 4:
                        _d.sent();
                        _d.label = 5;
                    case 5: 
                    // Return FundingAnalysis object to satisfy the base class requirement
                    return [2 /*return*/, {
                            topOpportunities: validRates,
                            statistics: {
                                totalPairs: rawData.length,
                                pairsWithFunding: validRates.length,
                                positiveRates: validRates.filter(function (r) { return r.predicted > 0; }).length,
                                negativeRates: validRates.filter(function (r) { return r.predicted < 0; }).length,
                                highestRate: validRates.length > 0 ? validRates.reduce(function (max, curr) {
                                    return Math.abs(curr.predicted) > Math.abs(max.predicted) ? curr : max;
                                }) : null,
                                averageRate: validRates.reduce(function (sum, rate) { return sum + rate.predicted; }, 0) / validRates.length || 0
                            }
                        }];
                    case 6:
                        error_2 = _d.sent();
                        this.log("Pipeline error: ".concat(error_2 instanceof Error ? error_2.message : String(error_2)), 'minimal');
                        throw error_2;
                    case 7: return [2 /*return*/];
                }
            });
        });
    };
    return SupabaseFundingPipeline;
}(funding_pipeline_1.FundingPipeline));
exports.SupabaseFundingPipeline = SupabaseFundingPipeline;
// Example usage
if (require.main === module) {
    var pipeline_1 = new SupabaseFundingPipeline({
        logLevel: 'verbose',
        updateInterval: 210000 // 3.5 minutes
    });
    // Handle graceful shutdown
    process.on('SIGINT', function () {
        console.log('\nReceived SIGINT. Shutting down gracefully...');
        pipeline_1.stop();
    });
    process.on('SIGTERM', function () {
        console.log('\nReceived SIGTERM. Shutting down gracefully...');
        pipeline_1.stop();
    });
    // Start the pipeline
    pipeline_1.start().catch(function (error) {
        console.error('Fatal pipeline error:', error);
        process.exit(1);
    });
}
