import { z } from 'zod'

const envSchema = z.object({
  SUPABASE_URL: z.string(),
  SUPABASE_SERVICE_KEY: z.string(),
  BIRDEYE_API_KEY: z.string(),
  NEXT_PUBLIC_BIRDEYE_API_KEY: z.string().optional(),
  NEXT_PUBLIC_SUPABASE_URL: z.string().optional(),
  NEXT_PUBLIC_SUPABASE_KEY: z.string().optional()
})

// Load from both process.env and .env
const combinedEnv = {
  SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
  BIRDEYE_API_KEY: process.env.NEXT_PUBLIC_BIRDEYE_API_KEY || process.env.BIRDEYE_API_KEY,
  ...process.env
}

// Validate and export
export const env = envSchema.parse(combinedEnv) 