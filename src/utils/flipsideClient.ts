import { Flipside, QueryResultsRpcResponse } from '@flipsidecrypto/sdk'

const flipside = new Flipside(
  process.env.NEXT_PUBLIC_FLIPSIDE_API_KEY!,
  'https://api.flipsidecrypto.com'
)

export async function runQuery(query: string): Promise<QueryResultsRpcResponse> {
  try {
    const result = await flipside.query.run({
      sql: query,
      timeoutMinutes: 5,
      cached: true
    })

    if (!result.success) {
      throw new Error(result.error || 'Query failed')
    }

    return result
  } catch (error) {
    console.error('Flipside query error:', error)
    throw error
  }
} 