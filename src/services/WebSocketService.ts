import { WebSocket } from 'ws';
import { EventEmitter } from 'events';
import { DataProvider, AssetType } from '../types/blockchain-analytics';
import { RedisCacheService } from './RedisCacheService';

interface WebSocketConfig {
  reconnectInterval: number;
  maxReconnectAttempts: number;
  pingInterval: number;
}

export class WebSocketService extends EventEmitter {
  private connections: Map<DataProvider, WebSocket>;
  private cache: RedisCacheService;
  private config: WebSocketConfig;
  private reconnectAttempts: Map<DataProvider, number>;

  constructor(cache: RedisCacheService, config?: Partial<WebSocketConfig>) {
    super();
    this.connections = new Map();
    this.cache = cache;
    this.reconnectAttempts = new Map();
    this.config = {
      reconnectInterval: config?.reconnectInterval || 5000,
      maxReconnectAttempts: config?.maxReconnectAttempts || 5,
      pingInterval: config?.pingInterval || 30000
    };
  }

  async connect(provider: DataProvider, url: string): Promise<void> {
    try {
      const ws = new WebSocket(url);
      
      ws.on('open', () => {
        console.log(`Connected to ${provider}`);
        this.connections.set(provider, ws);
        this.reconnectAttempts.set(provider, 0);
        this.startPingInterval(provider);
      });

      ws.on('message', async (data: string) => {
        try {
          const parsedData = JSON.parse(data);
          await this.handleMessage(provider, parsedData);
        } catch (error) {
          console.error(`Error handling message from ${provider}:`, error);
        }
      });

      ws.on('close', () => this.handleDisconnect(provider, url));
      ws.on('error', (error) => {
        console.error(`WebSocket error for ${provider}:`, error);
        this.handleDisconnect(provider, url);
      });

    } catch (error) {
      console.error(`Failed to connect to ${provider}:`, error);
      this.handleDisconnect(provider, url);
    }
  }

  private async handleMessage(provider: DataProvider, data: any): Promise<void> {
    // Cache the raw data
    const cacheKey = `ws:${provider}:${data.symbol || data.address}`;
    await this.cache.set(cacheKey, data, 300); // 5 minute TTL

    // Emit the processed data
    this.emit('data', {
      provider,
      timestamp: new Date(),
      data: this.processData(provider, data)
    });
  }

  private processData(provider: DataProvider, data: any): any {
    switch (provider) {
      case DataProvider.HYPERLIQUID:
        return this.processHyperliquidData(data);
      case DataProvider.DUNE:
        return this.processDuneData(data);
      // Add other providers...
      default:
        return data;
    }
  }

  private async handleDisconnect(provider: DataProvider, url: string): Promise<void> {
    const attempts = this.reconnectAttempts.get(provider) || 0;
    
    if (attempts < this.config.maxReconnectAttempts) {
      console.log(`Attempting to reconnect to ${provider}...`);
      this.reconnectAttempts.set(provider, attempts + 1);
      
      setTimeout(() => {
        this.connect(provider, url);
      }, this.config.reconnectInterval);
    } else {
      console.error(`Max reconnection attempts reached for ${provider}`);
      this.emit('maxReconnectAttemptsReached', provider);
    }
  }

  private startPingInterval(provider: DataProvider): void {
    const ws = this.connections.get(provider);
    if (!ws) return;

    setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.ping();
      }
    }, this.config.pingInterval);
  }

  private processHyperliquidData(data: any): any {
    // Process Hyperliquid-specific data format
    return {
      type: AssetType.PERPETUAL,
      symbol: data.symbol,
      price: parseFloat(data.mark_price),
      funding_rate: parseFloat(data.funding_rate),
      open_interest: parseFloat(data.open_interest),
      volume_24h: parseFloat(data.volume_24h),
      timestamp: new Date()
    };
  }

  private processDuneData(data: any): any {
    // Process Dune-specific data format
    return {
      type: AssetType.TOKEN,
      address: data.address,
      volume_24h: parseFloat(data.volume),
      unique_users: parseInt(data.users),
      timestamp: new Date()
    };
  }
} 