from typing import List, Dict, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
import logging

logger = logging.getLogger(__name__)

class MetricsFetcher:
    def __init__(self):
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase environment variables not set")
        self.supabase: Client = create_client(supabase_url, supabase_key)

    async def get_protocol_metrics(
        self, 
        protocol_name: Optional[str] = None,
        chain: Optional[str] = None,
        days: int = 7
    ) -> List[Dict]:
        """Fetch protocol metrics from Supabase"""
        try:
            query = self.supabase.table('nft_protocol_metrics')\
                .select('*')\
                .gte('created_at', datetime.utcnow() - timedelta(days=days))
            
            if protocol_name:
                query = query.eq('protocol_name', protocol_name)
            if chain:
                query = query.eq('chain', chain)
                
            result = await query.order('created_at', desc=True).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching protocol metrics: {str(e)}")
            return []

    async def get_chain_metrics(
        self,
        chain: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict]:
        """Fetch chain metrics from Supabase"""
        try:
            query = self.supabase.table('chain_metrics')\
                .select('*')\
                .gte('hour', datetime.utcnow() - timedelta(hours=hours))
            
            if chain:
                query = query.eq('chain', chain)
                
            result = await query.order('hour', desc=True).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching chain metrics: {str(e)}")
            return []

    async def get_nft_collection_metrics(
        self,
        collection_name: Optional[str] = None,
        days: int = 7
    ) -> List[Dict]:
        """Fetch NFT collection metrics from Supabase"""
        try:
            query = self.supabase.table('nft_collection_metrics')\
                .select('*')\
                .gte('period_start', datetime.utcnow() - timedelta(days=days))
            
            if collection_name:
                query = query.eq('collection_name', collection_name)
                
            result = await query.order('period_start', desc=True).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching NFT collection metrics: {str(e)}")
            return [] 