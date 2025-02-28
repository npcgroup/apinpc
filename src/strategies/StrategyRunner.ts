import { BaseStrategy } from './base_strategy';
import { createClient } from '@supabase/supabase-js';

interface StrategyRunnerConfig {
  supabaseUrl: string;
  supabaseKey: string;
  strategies: BaseStrategy[];
  executionIntervalMs: number;
  errorRetryCount: number;
  errorRetryDelayMs: number;
}

export class StrategyRunner {
  private strategies: BaseStrategy[];
  private isRunning: boolean = false;
  private executionInterval: number;
  private retryCount: number;
  private retryDelay: number;
  private executionTimer: NodeJS.Timeout | null = null;

  constructor(config: StrategyRunnerConfig) {
    this.strategies = config.strategies;
    this.executionInterval = config.executionIntervalMs;
    this.retryCount = config.errorRetryCount;
    this.retryDelay = config.errorRetryDelayMs;
  }

  async start(): Promise<void> {
    if (this.isRunning) {
      console.warn('Strategy runner is already running');
      return;
    }

    this.isRunning = true;
    console.log('Starting strategy runner...');

    try {
      // Initialize all strategies
      await Promise.all(
        this.strategies.map(strategy => 
          this.initializeWithRetry(strategy)
        )
      );

      // Start execution loop
      await this.executeLoop();
    } catch (error) {
      console.error('Failed to start strategy runner:', error);
      this.isRunning = false;
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (!this.isRunning) {
      console.warn('Strategy runner is not running');
      return;
    }

    console.log('Stopping strategy runner...');
    this.isRunning = false;

    if (this.executionTimer) {
      clearTimeout(this.executionTimer);
      this.executionTimer = null;
    }

    // Cleanup all strategies
    await Promise.all(
      this.strategies.map(strategy =>
        this.cleanupWithRetry(strategy)
      )
    );

    console.log('Strategy runner stopped');
  }

  private async executeLoop(): Promise<void> {
    while (this.isRunning) {
      const startTime = Date.now();

      try {
        await Promise.all(
          this.strategies.map(strategy =>
            this.executeWithRetry(strategy)
          )
        );
      } catch (error) {
        console.error('Error in strategy execution loop:', error);
      }

      const executionTime = Date.now() - startTime;
      const delayTime = Math.max(0, this.executionInterval - executionTime);

      if (this.isRunning) {
        this.executionTimer = setTimeout(
          () => this.executeLoop(),
          delayTime
        );
      }
    }
  }

  private async initializeWithRetry(
    strategy: BaseStrategy,
    attemptCount: number = 0
  ): Promise<void> {
    try {
      await strategy.initialize();
    } catch (error) {
      if (attemptCount < this.retryCount) {
        console.warn(
          `Failed to initialize strategy ${strategy.constructor.name}, retrying in ${this.retryDelay}ms...`,
          error
        );
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.initializeWithRetry(strategy, attemptCount + 1);
      }
      throw error;
    }
  }

  private async executeWithRetry(
    strategy: BaseStrategy,
    attemptCount: number = 0
  ): Promise<void> {
    try {
      await strategy.execute();
    } catch (error) {
      if (attemptCount < this.retryCount) {
        console.warn(
          `Failed to execute strategy ${strategy.constructor.name}, retrying in ${this.retryDelay}ms...`,
          error
        );
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.executeWithRetry(strategy, attemptCount + 1);
      }
      throw error;
    }
  }

  private async cleanupWithRetry(
    strategy: BaseStrategy,
    attemptCount: number = 0
  ): Promise<void> {
    try {
      await strategy.cleanup();
    } catch (error) {
      if (attemptCount < this.retryCount) {
        console.warn(
          `Failed to cleanup strategy ${strategy.constructor.name}, retrying in ${this.retryDelay}ms...`,
          error
        );
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.cleanupWithRetry(strategy, attemptCount + 1);
      }
      throw error;
    }
  }
} 