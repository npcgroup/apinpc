import { DataIngestionService } from '../services/dataIngestion';

async function testIngestion() {
  try {
    const service = new DataIngestionService();
    
    // Test connection first
    const isConnected = await service.testSupabaseConnection();
    console.log('Supabase connection test:', isConnected);
    
    if (!isConnected) {
      console.error('Failed to connect to Supabase. Check your credentials.');
      return;
    }
    
    // Run full ingestion
    const result = await service.fullIngestionProcess();
    console.log('Ingestion completed:', result);
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

testIngestion(); 