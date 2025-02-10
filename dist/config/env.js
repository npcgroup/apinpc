"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.env = void 0;
exports.validateConfig = validateConfig;
const zod_1 = require("zod");
const envSchema = zod_1.z.object({
    SUPABASE_URL: zod_1.z.string(),
    SUPABASE_SERVICE_KEY: zod_1.z.string(),
    SUPABASE_ANON_KEY: zod_1.z.string().optional(),
    BIRDEYE_API_KEY: zod_1.z.string(),
    NEXT_PUBLIC_BIRDEYE_API_KEY: zod_1.z.string().optional(),
    NEXT_PUBLIC_SUPABASE_URL: zod_1.z.string().optional(),
    NEXT_PUBLIC_SUPABASE_ANON_KEY: zod_1.z.string().optional()
});
// Load from both process.env and .env
const combinedEnv = {
    SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    BIRDEYE_API_KEY: process.env.NEXT_PUBLIC_BIRDEYE_API_KEY || process.env.BIRDEYE_API_KEY,
    ...process.env
};
// Validate and export
exports.env = envSchema.parse(combinedEnv);
function validateConfig() {
    const required = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'BIRDEYE_API_KEY'
    ];
    for (const key of required) {
        if (!exports.env[key]) {
            throw new Error(`Missing required environment variable: ${key}`);
        }
    }
}
