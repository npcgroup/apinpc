-- Run this in Supabase SQL editor
SELECT EXISTS (
   SELECT FROM information_schema.tables 
   WHERE table_name = 'token_metrics'
);

SELECT EXISTS (
   SELECT FROM information_schema.tables 
   WHERE table_name = 'dexscreener_pairs'
); 