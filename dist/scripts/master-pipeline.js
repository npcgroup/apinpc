"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MasterPipeline = void 0;
const supabase_js_1 = require("@supabase/supabase-js");
const child_process_1 = require("child_process");
const dotenv = __importStar(require("dotenv"));
const chalk_1 = __importDefault(require("chalk"));
const ora_1 = __importDefault(require("ora"));
const cli_table3_1 = __importDefault(require("cli-table3"));
const util_1 = require("util");
const path_1 = __importDefault(require("path"));
// Load environment variables first
dotenv.config({ path: path_1.default.resolve(__dirname, '../.env') });
// Validate environment variables
if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    throw new Error('NEXT_PUBLIC_SUPABASE_URL is not set in environment variables');
}
if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error('SUPABASE_SERVICE_ROLE_KEY is not set in environment variables');
}
// Initialize Supabase client after env vars are loaded
const supabase = (0, supabase_js_1.createClient)(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
const execAsync = (0, util_1.promisify)(child_process_1.exec);
class MasterPipeline {
    constructor() {
        this.isRunning = false;
        this.spinner = (0, ora_1.default)({ spinner: 'dots' });
        this.scripts = {
            binance_market: {
                command: ['python', 'scripts/binance_market_data.py'],
                description: '🔄 Binance Market Data',
                interval: 300,
                retryCount: 3,
                retryDelay: 60,
                dependencies: []
            },
            hyperliquid_funding: {
                command: ['python', 'scripts/push_hyperliquid_json_to_supabase.py'],
                description: '🌀 Hyperliquid Funding',
                interval: 600,
                retryCount: 3,
                retryDelay: 60,
                dependencies: []
            },
            binance_funding: {
                command: ['python', 'scripts/binance_funding_rates.py'],
                description: '📈 Binance Funding',
                interval: 600,
                retryCount: 3,
                retryDelay: 60,
                dependencies: []
            },
            bybit_market: {
                command: ['python', 'scripts/bybit_market_data.py'],
                description: '📊 Bybit Market',
                interval: 300,
                retryCount: 3,
                retryDelay: 60,
                dependencies: []
            },
            hl_funding: {
                command: ['ts-node', 'scripts/hl-funding.ts'],
                description: '⚡ HL Funding Analysis',
                interval: 900,
                retryCount: 3,
                retryDelay: 60,
                dependencies: ['hyperliquid_funding']
            },
            advanced_analysis: {
                command: ['python', 'scripts/advanced_funding_analyzer.py'],
                description: '🧠 Advanced Analysis',
                interval: 1200,
                retryCount: 3,
                retryDelay: 60,
                dependencies: ['binance_funding', 'hl_funding']
            }
        };
        this.status = Object.keys(this.scripts).reduce((acc, key) => ({
            ...acc,
            [key]: { errorCount: 0 }
        }), {});
    }
    checkDependencies(name) {
        return this.scripts[name].dependencies.every(dep => {
            const depStatus = this.status[dep];
            return depStatus.lastSuccess &&
                (Date.now() - depStatus.lastSuccess.getTime() <= this.scripts[dep].interval * 2000);
        });
    }
    async runScript(name) {
        const script = this.scripts[name];
        if (!this.checkDependencies(name)) {
            console.log(chalk_1.default.yellow(`Dependencies not met for ${script.description}`));
            return false;
        }
        for (let attempt = 0; attempt < script.retryCount; attempt++) {
            try {
                this.spinner.start(`Running ${script.description}`);
                const result = await execAsync(script.command.join(' '));
                // Log output for debugging if needed
                if (result.stdout)
                    console.log(chalk_1.default.dim(result.stdout));
                this.status[name].lastSuccess = new Date();
                this.status[name].errorCount = 0;
                this.spinner.succeed(`${script.description} completed`);
                return true;
            }
            catch (error) {
                this.status[name].errorCount++;
                this.spinner.fail(`${script.description} failed (attempt ${attempt + 1}/${script.retryCount})`);
                if (error instanceof Error) {
                    console.error(chalk_1.default.red(error.message));
                }
                if (attempt < script.retryCount - 1) {
                    this.spinner.start(`Waiting ${script.retryDelay}s before retry...`);
                    await new Promise(resolve => setTimeout(resolve, script.retryDelay * 1000));
                }
            }
        }
        return false;
    }
    renderStatus() {
        console.clear();
        // Calculate progress
        const total = Object.keys(this.scripts).length;
        const completed = Object.values(this.status).filter(s => s.lastSuccess && (Date.now() - s.lastSuccess.getTime() <= 600000)).length;
        // Progress bar
        const width = 50;
        const filled = Math.round((completed / total) * width);
        const progress = '█'.repeat(filled) + '░'.repeat(width - filled);
        console.log(chalk_1.default.cyan('\n🚀 Pipeline Status'));
        console.log(chalk_1.default.blue(`Progress: ${progress} ${Math.round((completed / total) * 100)}%\n`));
        // Status table
        const table = new cli_table3_1.default({
            head: ['Script', 'Status', 'Last Success', 'Errors'],
            style: { head: ['cyan'] }
        });
        Object.entries(this.scripts).forEach(([name, script]) => {
            const status = this.status[name];
            const lastSuccess = status.lastSuccess ?
                status.lastSuccess.toLocaleTimeString() : 'Never';
            table.push([
                script.description,
                status.lastSuccess ? chalk_1.default.green('ACTIVE') : chalk_1.default.yellow('PENDING'),
                lastSuccess,
                status.errorCount > 0 ? chalk_1.default.red(status.errorCount) : chalk_1.default.green('0')
            ]);
        });
        console.log(table.toString());
    }
    async start() {
        console.log(chalk_1.default.cyan('\n🚀 Starting Pipeline'));
        this.isRunning = true;
        while (this.isRunning) {
            this.renderStatus();
            for (const [name, script] of Object.entries(this.scripts)) {
                const status = this.status[name];
                const timeSinceLastRun = status.lastRun ?
                    Date.now() - status.lastRun.getTime() : Infinity;
                if (timeSinceLastRun >= script.interval * 1000) {
                    this.status[name].lastRun = new Date();
                    await this.runScript(name);
                }
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    stop() {
        this.isRunning = false;
        this.spinner.stop();
        console.log(chalk_1.default.yellow('\nPipeline shutdown requested'));
    }
}
exports.MasterPipeline = MasterPipeline;
if (require.main === module) {
    const pipeline = new MasterPipeline();
    process.on('SIGINT', () => {
        pipeline.stop();
        process.exit(0);
    });
    process.on('SIGTERM', () => {
        pipeline.stop();
        process.exit(0);
    });
    pipeline.start().catch(error => {
        console.error(chalk_1.default.red('Fatal error:'), error);
        process.exit(1);
    });
}
