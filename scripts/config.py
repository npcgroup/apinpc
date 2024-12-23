import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging
from typing import Optional

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        DATABASE_URL = f"postgresql://{os.getenv('SUPABASE_DB_USER')}:{os.getenv('SUPABASE_DB_PASSWORD')}@{os.getenv('SUPABASE_DB_HOST')}/{os.getenv('SUPABASE_DB_NAME')}"
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        logger.info("Successfully connected to database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise