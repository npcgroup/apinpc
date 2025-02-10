"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supabase_js_1 = require("@supabase/supabase-js");
const fs_1 = require("fs");
const path_1 = __importDefault(require("path"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config({ path: '.env.local' });
async function migrateSchema() {
    const supabase = (0, supabase_js_1.createClient)(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
    try {
        // First create the exec_migration function
        const functionSqlPath = path_1.default.join(__dirname, '../../supabase/migrations/create_exec_migration_function.sql');
        const functionSql = (0, fs_1.readFileSync)(functionSqlPath, 'utf8');
        console.log('Creating exec_migration function...');
        const { error: functionError } = await supabase.rpc('exec_sql', {
            query: functionSql
        });
        if (functionError) {
            throw functionError;
        }
        // Then run the schema transformation
        console.log('Transforming schema...');
        const transformSqlPath = path_1.default.join(__dirname, '../../supabase/migrations/transform_existing_schema.sql');
        const transformSql = (0, fs_1.readFileSync)(transformSqlPath, 'utf8');
        const { error: transformError } = await supabase.rpc('exec_migration', {
            sql: transformSql
        });
        if (transformError) {
            throw transformError;
        }
        console.log('Schema migration completed successfully');
    }
    catch (error) {
        console.error('Error during schema migration:', error);
        process.exit(1);
    }
}
migrateSchema();
