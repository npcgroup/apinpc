import { createClient } from '@supabase/supabase-js';
import { readFileSync } from 'fs';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config({ path: '.env.local' });

async function migrateSchema() {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  try {
    // First create the exec_migration function
    const functionSqlPath = path.join(__dirname, '../../supabase/migrations/create_exec_migration_function.sql');
    const functionSql = readFileSync(functionSqlPath, 'utf8');

    console.log('Creating exec_migration function...');
    const { error: functionError } = await supabase.rpc('exec_sql', { 
      query: functionSql 
    });

    if (functionError) {
      throw functionError;
    }

    // Then run the schema transformation
    console.log('Transforming schema...');
    const transformSqlPath = path.join(__dirname, '../../supabase/migrations/transform_existing_schema.sql');
    const transformSql = readFileSync(transformSqlPath, 'utf8');

    const { error: transformError } = await supabase.rpc('exec_migration', { 
      sql: transformSql 
    });
    
    if (transformError) {
      throw transformError;
    }
    
    console.log('Schema migration completed successfully');
  } catch (error) {
    console.error('Error during schema migration:', error);
    process.exit(1);
  }
}

migrateSchema(); 