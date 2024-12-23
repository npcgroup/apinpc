export const config = {
  dune: {
    apiKey: process.env.NEXT_PUBLIC_DUNE_API_KEY || process.env.DUNE_API_KEY
  },
  flipside: {
    apiKey: process.env.NEXT_PUBLIC_FLIPSIDE_API_KEY || process.env.FLIPSIDE_API_KEY
  }
};

export function validateConfig() {
  const missingVars = [];
  
  if (!config.dune.apiKey) {
    missingVars.push('NEXT_PUBLIC_DUNE_API_KEY');
  }
  if (!config.flipside.apiKey) {
    missingVars.push('NEXT_PUBLIC_FLIPSIDE_API_KEY');
  }

  if (missingVars.length > 0) {
    console.error(`Missing required environment variables: ${missingVars.join(', ')}`);
    return false;
  }

  return true;
} 