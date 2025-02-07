import { createClient } from '@supabase/supabase-js';
import { exec } from 'child_process';
import * as dotenv from 'dotenv';
import chalk from 'chalk';
import ora from 'ora';
import Table from 'cli-table3';
import { promisify } from 'util';
import type { Ora } from 'ora';
import path from 'path';

// Load environment variables first
dotenv.config({ path: path.resolve(__dirname, '../.env') });

// Validate environment variables
if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    throw new Error('NEXT_PUBLIC_SUPABASE_URL is not set in environment variables');
}
if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error('SUPABASE_SERVICE_ROLE_KEY is not set in environment variables');
}

// Initialize Supabase client after env vars are loaded
const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

const execAsync = promisify(exec);

interface Script {
    command: string[];
    description: string;
    interval: number;
    retryCount: number;
    retryDelay: number;
    dependencies: string[];
}

interface ScriptStatus {
    lastRun?: Date;
    lastSuccess?: Date;
    errorCount: number;
}

interface ExecResult {
    stdout: string;
    stderr: string;
}

class MasterPipeline {
    private scripts: Record<string, Script>;
    private status: Record<string, ScriptStatus>;
    private isRunning: boolean = false;
    private spinner: Ora;

    constructor() {
        this.spinner = ora({ spinner: 'dots' });
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

        this.status = Object.keys(this.scripts).reduce<Record<string, ScriptStatus>>((acc, key) => ({
            ...acc,
            [key]: { errorCount: 0 }
        }), {});
    }

    private checkDependencies(name: string): boolean {
        return this.scripts[name].dependencies.every(dep => {
            const depStatus = this.status[dep];
            return depStatus.lastSuccess && 
                   (Date.now() - depStatus.lastSuccess.getTime() <= this.scripts[dep].interval * 2000);
        });
    }

    private async runScript(name: string): Promise<boolean> {
        const script = this.scripts[name];
        
        if (!this.checkDependencies(name)) {
            console.log(chalk.yellow(`Dependencies not met for ${script.description}`));
            return false;
        }

        for (let attempt = 0; attempt < script.retryCount; attempt++) {
            try {
                this.spinner.start(`Running ${script.description}`);
                const result: ExecResult = await execAsync(script.command.join(' '));
                
                // Log output for debugging if needed
                if (result.stdout) console.log(chalk.dim(result.stdout));
                
                this.status[name].lastSuccess = new Date();
                this.status[name].errorCount = 0;
                this.spinner.succeed(`${script.description} completed`);
                return true;

            } catch (error) {
                this.status[name].errorCount++;
                this.spinner.fail(`${script.description} failed (attempt ${attempt + 1}/${script.retryCount})`);
                
                if (error instanceof Error) {
                    console.error(chalk.red(error.message));
                }
                
                if (attempt < script.retryCount - 1) {
                    this.spinner.start(`Waiting ${script.retryDelay}s before retry...`);
                    await new Promise(resolve => setTimeout(resolve, script.retryDelay * 1000));
                }
            }
        }

        return false;
    }

    private renderStatus(): void {
        console.clear();
        
        // Calculate progress
        const total = Object.keys(this.scripts).length;
        const completed = Object.values(this.status).filter(s => 
            s.lastSuccess && (Date.now() - s.lastSuccess.getTime() <= 600000)
        ).length;
        
        // Progress bar
        const width = 50;
        const filled = Math.round((completed / total) * width);
        const progress = '█'.repeat(filled) + '░'.repeat(width - filled);
        
        console.log(chalk.cyan('\n🚀 Pipeline Status'));
        console.log(chalk.blue(`Progress: ${progress} ${Math.round((completed / total) * 100)}%\n`));

        // Status table
        const table = new Table({
            head: ['Script', 'Status', 'Last Success', 'Errors'],
            style: { head: ['cyan'] }
        });

        Object.entries(this.scripts).forEach(([name, script]) => {
            const status = this.status[name];
            const lastSuccess = status.lastSuccess ? 
                status.lastSuccess.toLocaleTimeString() : 'Never';
            
            table.push([
                script.description,
                status.lastSuccess ? chalk.green('ACTIVE') : chalk.yellow('PENDING'),
                lastSuccess,
                status.errorCount > 0 ? chalk.red(status.errorCount) : chalk.green('0')
            ]);
        });

        console.log(table.toString());
    }

    public async start(): Promise<void> {
        console.log(chalk.cyan('\n🚀 Starting Pipeline'));
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

    public stop(): void {
        this.isRunning = false;
        this.spinner.stop();
        console.log(chalk.yellow('\nPipeline shutdown requested'));
    }
}

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
        console.error(chalk.red('Fatal error:'), error);
        process.exit(1);
    });
}

export { MasterPipeline };