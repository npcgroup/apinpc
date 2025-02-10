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
exports.FundingStorage = void 0;
var promises_1 = require("fs/promises");
var path_1 = require("path");
var FundingStorage = /** @class */ (function () {
    function FundingStorage(options) {
        this.directory = options.directory;
        this.maxHistoryItems = options.maxHistoryItems || 1000;
    }
    FundingStorage.prototype.saveAnalysis = function (analysis) {
        return __awaiter(this, void 0, void 0, function () {
            var timestamp, filename, filepath;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        timestamp = new Date().toISOString();
                        filename = "funding-analysis-".concat(timestamp, ".json");
                        filepath = path_1.default.join(this.directory, filename);
                        return [4 /*yield*/, promises_1.default.mkdir(this.directory, { recursive: true })];
                    case 1:
                        _a.sent();
                        return [4 /*yield*/, promises_1.default.writeFile(filepath, JSON.stringify({
                                timestamp: timestamp,
                                analysis: analysis
                            }, null, 2))];
                    case 2:
                        _a.sent();
                        // Cleanup old files if needed
                        return [4 /*yield*/, this.cleanup()];
                    case 3:
                        // Cleanup old files if needed
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    FundingStorage.prototype.getLatestAnalysis = function () {
        return __awaiter(this, void 0, void 0, function () {
            var files, latest, content;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, promises_1.default.readdir(this.directory)];
                    case 1:
                        files = _a.sent();
                        latest = files
                            .filter(function (f) { return f.startsWith('funding-analysis-'); })
                            .sort()
                            .pop();
                        if (!latest)
                            return [2 /*return*/, null];
                        return [4 /*yield*/, promises_1.default.readFile(path_1.default.join(this.directory, latest), 'utf-8')];
                    case 2:
                        content = _a.sent();
                        return [2 /*return*/, JSON.parse(content)];
                }
            });
        });
    };
    FundingStorage.prototype.cleanup = function () {
        return __awaiter(this, void 0, void 0, function () {
            var files, analysisFiles, filesToDelete;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, promises_1.default.readdir(this.directory)];
                    case 1:
                        files = _a.sent();
                        analysisFiles = files
                            .filter(function (f) { return f.startsWith('funding-analysis-'); })
                            .sort();
                        if (!(analysisFiles.length > this.maxHistoryItems)) return [3 /*break*/, 3];
                        filesToDelete = analysisFiles.slice(0, analysisFiles.length - this.maxHistoryItems);
                        return [4 /*yield*/, Promise.all(filesToDelete.map(function (file) {
                                return promises_1.default.unlink(path_1.default.join(_this.directory, file));
                            }))];
                    case 2:
                        _a.sent();
                        _a.label = 3;
                    case 3: return [2 /*return*/];
                }
            });
        });
    };
    return FundingStorage;
}());
exports.FundingStorage = FundingStorage;
