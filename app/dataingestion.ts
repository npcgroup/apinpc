import { supabase } from '@/lib/supabaseClient';
import { formatNumber, formatDate } from '@/utils/formatters';

// Add type definitions
interface ApiData {
  id?: number;
  [key: string]: any;
}

interface InsertResponse {
  success: boolean;
  data?: ApiData[];
  error?: string;
}

// Add the missing formatTableData function
export const formatTableData = (data: Record<string, unknown>[]) => {
  return {
    columns: Object.keys(data[0] || {}),
    rows: data.map(item => Object.values(item)),
    summary: {
      total: data.length,
      timestamp: new Date().toISOString()
    }
  };
};

// Update the insert function with proper types and error handling
export async function insertApiData(
  tableName: string,
  data: ApiData | ApiData[]
): Promise<InsertResponse> {
  try {
    const dataArray = Array.isArray(data) ? data : [data];

    // Fix the insert operation
    const { data: insertedData, error } = await supabase
      .from(tableName)
      .insert(dataArray)
      .select(); // Use select() instead of returning

    if (error) {
      throw error;
    }

    // Add null check for insertedData
    if (!insertedData) {
      throw new Error('No data was inserted');
    }

    return {
      success: true,
      data: insertedData
    };

  } catch (error) {
    console.error('Error inserting data:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

// Add a function to fetch data with proper typing
export async function fetchApiData(tableName: string) {
  try {
    const { data, error } = await supabase
      .from(tableName)
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      throw error;
    }

    return {
      success: true,
      data: data || []
    };

  } catch (error) {
    console.error('Error fetching data:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

// Add a function to create tables dynamically
export async function createTable(tableName: string, columns: Record<string, string>) {
  const columnDefinitions = Object.entries(columns)
    .map(([name, type]) => `${name} ${type}`)
    .join(', ');

  const query = `
    CREATE TABLE IF NOT EXISTS ${tableName} (
      id SERIAL PRIMARY KEY,
      ${columnDefinitions},
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
  `;

  try {
    const { error } = await supabase.rpc('create_table', { query_text: query });
    
    if (error) {
      throw error;
    }

    return {
      success: true
    };

  } catch (error) {
    console.error('Error creating table:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}