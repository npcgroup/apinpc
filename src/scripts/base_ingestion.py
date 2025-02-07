import json
from datetime import datetime
from pathlib import Path
from config import get_db_connection, logger

class BaseIngestion:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        
    def save_to_json(self, data: dict, data_type: str):
        """Save data to JSON file with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = Path("data") / data_type
        data_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{data_type}_{timestamp}.json"
        with open(data_dir / filename, "w") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Saved {data_type} data to {filename}")
        
    def __del__(self):
        """Clean up database connections"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close() 