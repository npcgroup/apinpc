"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FundingStorage = void 0;
const promises_1 = __importDefault(require("fs/promises"));
const path_1 = __importDefault(require("path"));
class FundingStorage {
    constructor(options) {
        this.directory = options.directory;
        this.maxHistoryItems = options.maxHistoryItems || 1000;
    }
    async saveAnalysis(analysis) {
        const timestamp = new Date().toISOString();
        const filename = `funding-analysis-${timestamp}.json`;
        const filepath = path_1.default.join(this.directory, filename);
        await promises_1.default.mkdir(this.directory, { recursive: true });
        await promises_1.default.writeFile(filepath, JSON.stringify({
            timestamp,
            analysis
        }, null, 2));
        // Cleanup old files if needed
        await this.cleanup();
    }
    async getLatestAnalysis() {
        const files = await promises_1.default.readdir(this.directory);
        const latest = files
            .filter(f => f.startsWith('funding-analysis-'))
            .sort()
            .pop();
        if (!latest)
            return null;
        const content = await promises_1.default.readFile(path_1.default.join(this.directory, latest), 'utf-8');
        return JSON.parse(content);
    }
    async cleanup() {
        const files = await promises_1.default.readdir(this.directory);
        const analysisFiles = files
            .filter(f => f.startsWith('funding-analysis-'))
            .sort();
        if (analysisFiles.length > this.maxHistoryItems) {
            const filesToDelete = analysisFiles.slice(0, analysisFiles.length - this.maxHistoryItems);
            await Promise.all(filesToDelete.map(file => promises_1.default.unlink(path_1.default.join(this.directory, file))));
        }
    }
}
exports.FundingStorage = FundingStorage;
