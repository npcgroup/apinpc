import os
import requests
import time
from typing import Dict, List, Optional, TypedDict
from datetime import datetime
import logging
import json
from rich.console import Console
from rich.table import Table
from pathlib import Path
from dotenv import load_dotenv
from base_ingestion import BaseIngestion

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class FlipsideIngestion(BaseIngestion):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("NEXT_PUBLIC_FLIPSIDE_API_KEY")
        self.base_url = "https://api.flipsidecrypto.com"
        
    def get_metrics(self) -> Dict:
        """Fetch metrics from Flipside"""
        try:
            headers = {
                "x-api-key": self.api_key
            }
            response = requests.get(f"{self.base_url}/v1/metrics", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching Flipside metrics: {str(e)}")
            return {}

    def save_metrics(self, metrics: Dict):
        """Save metrics to JSON and database"""
        try:
            # Save to JSON
            self.save_to_json(metrics, "flipside")
            
            # Save to database using parent class method
            if metrics:
                sql = """
                INSERT INTO flipside_metrics 
                (data, created_at) 
                VALUES (%s, %s)
                """
                self.cursor.execute(sql, (json.dumps(metrics), datetime.now()))
                self.conn.commit()
                logger.info("Saved Flipside metrics to database")
                
        except Exception as e:
            logger.error(f"Error saving Flipside metrics: {str(e)}")
            self.conn.rollback()
            raise

if __name__ == "__main__":
    ingestion = FlipsideIngestion()
    metrics = ingestion.get_metrics()
    if metrics:
        ingestion.save_metrics(metrics)
    else:
        logger.warning("No Flipside metrics collected") 