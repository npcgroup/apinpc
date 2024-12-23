/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'lucide-react': require.resolve('lucide-react'),
    };
    return config;
  },
  env: {
    NEXT_PUBLIC_DUNE_API_KEY: process.env.NEXT_PUBLIC_DUNE_API_KEY,
    NEXT_PUBLIC_FLIPSIDE_API_KEY: process.env.NEXT_PUBLIC_FLIPSIDE_API_KEY,
  },
  serverRuntimeConfig: {
    DUNE_API_KEY: process.env.NEXT_PUBLIC_DUNE_API_KEY,
    FLIPSIDE_API_KEY: process.env.NEXT_PUBLIC_FLIPSIDE_API_KEY,
  },
  publicRuntimeConfig: {
    NEXT_PUBLIC_DUNE_API_KEY: process.env.NEXT_PUBLIC_DUNE_API_KEY,
    NEXT_PUBLIC_FLIPSIDE_API_KEY: process.env.NEXT_PUBLIC_FLIPSIDE_API_KEY,
  }
};

export default nextConfig; 