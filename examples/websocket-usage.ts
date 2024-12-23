import { WebSocketService } from '../services/WebSocketService';
import { RedisCacheService } from '../services/RedisCacheService';
import { DataProvider } from '../types/blockchain-analytics';

async function setupWebSockets() {
  const cache = new RedisCacheService({
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    password: process.env.REDIS_PASSWORD,
    keyPrefix: 'blockchain:'
  });

  const ws = new WebSocketService(cache, {
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
    pingInterval: 30000
  });

  // Handle incoming data
  ws.on('data', async ({ provider, timestamp, data }) => {
    console.log(`Received data from ${provider} at ${timestamp}:`, data);
    // Process real-time updates...
  });

  // Connect to data providers
  await ws.connect(
    DataProvider.HYPERLIQUID,
    'wss://api.hyperliquid.xyz/ws'
  );

  await ws.connect(
    DataProvider.DUNE,
    'wss://api.dune.com/v1/ws'
  );
}

setupWebSockets().catch(console.error); 