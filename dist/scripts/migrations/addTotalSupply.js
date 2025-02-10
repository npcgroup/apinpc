"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supabase_js_1 = require("@supabase/supabase-js");
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config({ path: '.env.local' });
async function addTotalSupplyColumn() {
    const supabase = (0, supabase_js_1.createClient)(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
    try {
        const { error } = await supabase.rpc('add_total_supply_column', {
            sql: `
        ALTER TABLE token_metrics 
        ADD COLUMN IF NOT EXISTS totalSupply NUMERIC;
        
        COMMENT ON COLUMN token_metrics.totalSupply IS 'Total supply of the token';
      `
        });
        if (error)
            throw error;
        console.log('Successfully added totalSupply column');
    }
    catch (error) {
        console.error('Error adding totalSupply column:', error);
    }
}
addTotalSupplyColumn();
