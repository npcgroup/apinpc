# Authentication

## Overview

Different platforms use different authentication methods:

### Dune Analytics
- Uses API key authentication
- API key should be passed in the `X-Dune-API-Key` header
- Keys can be generated from the Dune dashboard

### Bitquery
- Uses OAuth2 Bearer token authentication
- Format: `Bearer ory_...yourtoken`
- Tokens must be included in the Authorization header

### Subgraph APIs
- Generally use API key or token-based authentication
- Keys are specific to each subgraph deployment
- Some public endpoints may not require authentication

## Best Practices

1. Never expose API keys in client-side code
2. Rotate keys periodically
3. Use environment variables to store keys
4. Create separate keys for development and production
5. Monitor key usage and implement rate limiting 