export const getApiKeys = () => {
  const duneKey = process.env.NEXT_PUBLIC_DUNE_API_KEY;
  const flipsideKey = process.env.NEXT_PUBLIC_FLIPSIDE_API_KEY;

  if (!duneKey) {
    throw new Error('NEXT_PUBLIC_DUNE_API_KEY is not set');
  }

  if (!flipsideKey) {
    throw new Error('NEXT_PUBLIC_FLIPSIDE_API_KEY is not set');
  }

  return {
    dune: duneKey,
    flipside: flipsideKey
  };
}; 