import fs from 'fs/promises';
import path from 'path';

interface StorageOptions {
    directory: string;
    maxHistoryItems?: number;
}

export class FundingStorage {
    private directory: string;
    private maxHistoryItems: number;

    constructor(options: StorageOptions) {
        this.directory = options.directory;
        this.maxHistoryItems = options.maxHistoryItems || 1000;
    }

    async saveAnalysis(analysis: any) {
        const timestamp = new Date().toISOString();
        const filename = `funding-analysis-${timestamp}.json`;
        const filepath = path.join(this.directory, filename);

        await fs.mkdir(this.directory, { recursive: true });
        await fs.writeFile(filepath, JSON.stringify({
            timestamp,
            analysis
        }, null, 2));

        // Cleanup old files if needed
        await this.cleanup();
    }

    async getLatestAnalysis() {
        const files = await fs.readdir(this.directory);
        const latest = files
            .filter(f => f.startsWith('funding-analysis-'))
            .sort()
            .pop();

        if (!latest) return null;

        const content = await fs.readFile(path.join(this.directory, latest), 'utf-8');
        return JSON.parse(content);
    }

    private async cleanup() {
        const files = await fs.readdir(this.directory);
        const analysisFiles = files
            .filter(f => f.startsWith('funding-analysis-'))
            .sort();

        if (analysisFiles.length > this.maxHistoryItems) {
            const filesToDelete = analysisFiles.slice(0, analysisFiles.length - this.maxHistoryItems);
            await Promise.all(
                filesToDelete.map(file => 
                    fs.unlink(path.join(this.directory, file))
                )
            );
        }
    }
} 