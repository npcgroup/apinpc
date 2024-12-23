import { NextApiRequest, NextApiResponse } from 'next'
import { DataIngestionService } from '@/services/dataIngestion'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    console.log('API: Starting ingestion process...');
    const ingestionService = new DataIngestionService()
    const result = await ingestionService.fullIngestionProcess()
    
    console.log('API: Ingestion completed successfully:', result);
    res.status(200).json(result)
  } catch (error) {
    console.error('API: Error during ingestion:', error);
    res.status(500).json({ 
      message: 'Internal server error',
      error: error instanceof Error ? error.message : 'Unknown error',
      details: error instanceof Error ? error : undefined
    })
  }
} 