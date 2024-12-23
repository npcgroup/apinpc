import Redis from 'ioredis';
import { promisify } from 'util';

interface CacheConfig {
  host: string;
  port: number;
  password?: string;
  db?: number;
  keyPrefix?: string;
}

export class RedisCacheService {
  private redis: Redis;
  private keyPrefix: string;

  constructor(config: CacheConfig) {
    this.redis = new Redis({
      host: config.host,
      port: config.port,
      password: config.password,
      db: config.db || 0
    });
    this.keyPrefix = config.keyPrefix || 'blockchain:';
  }

  async get<T>(key: string): Promise<T | null> {
    const data = await this.redis.get(this.getKey(key));
    if (!data) return null;
    return JSON.parse(data);
  }

  async set(key: string, value: any, ttlSeconds?: number): Promise<void> {
    const serialized = JSON.stringify(value);
    if (ttlSeconds) {
      await this.redis.setex(this.getKey(key), ttlSeconds, serialized);
    } else {
      await this.redis.set(this.getKey(key), serialized);
    }
  }

  async delete(key: string): Promise<void> {
    await this.redis.del(this.getKey(key));
  }

  async exists(key: string): Promise<boolean> {
    const result = await this.redis.exists(this.getKey(key));
    return result === 1;
  }

  async getOrSet<T>(
    key: string,
    fetchFn: () => Promise<T>,
    ttlSeconds?: number
  ): Promise<T> {
    const cached = await this.get<T>(key);
    if (cached) return cached;

    const fresh = await fetchFn();
    await this.set(key, fresh, ttlSeconds);
    return fresh;
  }

  private getKey(key: string): string {
    return `${this.keyPrefix}${key}`;
  }

  async disconnect(): Promise<void> {
    await this.redis.quit();
  }
} 