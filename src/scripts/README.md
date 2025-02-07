# Blockchain Analytics Data Pipeline

![Pipeline Architecture](https://mermaid.ink/svg/pako:eNpNkE1PwzAMhv9KlVOnHd0H4gQSEkJi4sIBpK5JN6VJm4R1CPHfOZ0Q6vRky_v6tZ3Y0a6xQ1V3Vjq4Qm0H6eD5dX0qy7J8eX4o3mBvB9mBdHXj4AqV7aWDt9fNqSzLzXpVfMDeDrID6erGwRUq20sHm9W6LMv1aln8wN4OsgPp6sbBFSrbSwfPm4_Ndrvdrh6LL9jbQXYgXd04uEJle-ngD3X3BzXUJBs)

## 📋 Overview
This repository contains a suite of tools for real-time blockchain analytics with a focus on perpetual futures markets. The scripts handle:

1. **Multi-exchange data ingestion** (Binance, Bybit, Hyperliquid, Birdeye)
2. **Funding rate arbitrage detection**
3. **Market data analysis & visualization**
4. **Supabase database integration**
5. **Predictive analytics for funding rates**

## 🛠 Prerequisites

### Environment Setup
```bash
cp .env.example .env
# Fill in all API keys (see .env example below)
```

```env:.env
NEXT_PUBLIC_BIRDEYE_API_KEY=your_key
NEXT_PUBLIC_SUPABASE_URL=your_url
NEXT_PUBLIC_SUPABASE_KEY=your_key
# ... 15+ other keys from provided snippets
```

### Dependencies
```bash
pip install -r requirements.txt
yarn install
```

## 🧰 Script Categories

### 1. Data Ingestion
| Script | Purpose | Run Command |
|--------|---------|-------------|
| `binance_funding_rates.py` | Fetch Binance perpetual futures data | `python scripts/binance_funding_rates.py` |
| `bybit_market_data.py` | Bybit market data collector | `python scripts/bybit_market_data.py` |
| `birdeye.py` | Solana token metrics | `python scripts/birdeye.py` |
| `hyperliquid_api.ts` | Hyperliquid funding rates | `ts-node scripts/hyperliquid_api.ts` |

```python:scripts/binance_funding_rates.py
startLine: 1
endLine: 90
```

### 2. Funding Rate Analysis
| Script | Purpose | Run Command |
|--------|---------|-------------|
| `advanced_funding_analyzer.py` | Cross-exchange arbitrage detection | `python scripts/advanced_funding_analyzer.py` |
| `enhanced_funding_predictor.py` | Rate predictions | `python scripts/enhanced_funding_predictor.py` |
| `funding-pipeline.ts` | Continuous rate monitoring | `ts-node scripts/funding-pipeline.ts` |

```python:scripts/advanced_funding_analyzer.py
startLine: 1
endLine: 341
```

### 3. Database Integration
| Script | Purpose | Run Command |
|--------|---------|-------------|
| `supabase_funding.ts` | Store opportunities | `ts-node scripts/supabase_funding.ts` |
| `base_ingestion.py` | Base DB class | Inherited by ingestors |

```typescript:scripts/funding-pipeline-supabase.ts
startLine: 1
endLine: 45
```

### 4. Analytics & Visualization
| Script | Purpose | Run Command |
|--------|---------|-------------|
| `analyze_funding_rates.py` | Historical analysis | `python scripts/analyze_funding_rates.py` |
| `market_visualizer.py` | Real-time dashboards | `python scripts/market_visualizer.py` |

## 🚀 Example Workflow

1. Start data ingestion:
```bash
# Binance perpetuals
python scripts/binance_funding_rates.py &

# Bybit markets
python scripts/bybit_market_data.py &

# Hyperliquid funding
ts-node scripts/hyperliquid_api.ts &
```

2. Run arbitrage detection:
```bash
python scripts/advanced_funding_analyzer.py \
  --threshold 0.0005 \
  --leverage 10 \
  --output-dir ./arbitrage_ops
```

3. Monitor predictions:
```bash
python scripts/enhanced_funding_predictor.py \
  --horizon 8 \
  --min-confidence 0.8
```

## 🔑 Key Features

1. **Multi-Exchange Support**
   - Binance, Bybit, Hyperliquid, Birdeye
   - Unified data models across exchanges

2. **Predictive Analytics**
   - Funding rate forecasting
   - Annualized return calculations
   - Risk-adjusted opportunity scoring

3. **Database Integration**
   - Automatic Supabase synchronization
   - Historical data archiving
   - Efficient upsert operations

4. **Production-Ready**
   - Rate limiting
   - Error handling
   - Rich terminal output
   - Configurable logging

## 📈 Sample Output

```bash
🌟 Top Funding Rate Opportunities 🌟
================================================
Market     HL Rate   Binance Rate     Spread  Annual %
BTC        0.0032%      -0.0018%      0.0050%  182.5%
ETH       -0.0021%      -0.0045%      0.0024%   87.6%
SOL        0.0045%       0.0012%      0.0033%  120.4%
```

## 🛑 Important Notes

1. Configure all API keys in `.env`
2. Run database migrations first
3. Monitor rate limits (especially Binance)
4. Use `--help` on any script for options
5. Store sensitive keys in Vault before production

This system provides institutional-grade market analysis tools for cryptocurrency perpetual futures markets. The modular design allows customization while maintaining robust data integrity and performance characteristics needed for algorithmic trading systems.