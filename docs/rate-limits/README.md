# Rate Limits & Quotas

## Dune Analytics
- Rate limits based on subscription tier
- Limits apply to:
  - Queries per minute
  - Data points accessed
  - Concurrent executions

## Bitquery
- Tiered rate limiting based on subscription
- Limits on:
  - Websocket connections
  - API calls per second
  - Data volume per request

## Best Practices
1. Implement exponential backoff
2. Cache frequently accessed data
3. Use batch requests where possible
4. Monitor usage against quotas
5. Implement client-side rate limiting 