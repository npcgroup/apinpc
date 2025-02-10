"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ENV = void 0;
const dotenv_1 = require("dotenv");
const path_1 = require("path");
const result = (0, dotenv_1.config)({
    path: (0, path_1.resolve)(__dirname, '../../../.env')
});
if (result.error) {
    console.error('Error loading .env file:', result.error);
    process.exit(1);
}
exports.ENV = {
    SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    SUPABASE_KEY: process.env.NEXT_PUBLIC_SUPABASE_KEY
};
// Validate required environment variables
Object.entries(exports.ENV).forEach(([key, value]) => {
    if (!value) {
        throw new Error(`Missing required environment variable: ${key}`);
    }
});
