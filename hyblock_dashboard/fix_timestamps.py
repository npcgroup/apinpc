#!/usr/bin/env python3
import os
import json
import pandas as pd
from datetime import datetime
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("fix_timestamps")

def fix_unix_timestamps():
    """
    Find and fix Unix timestamps that are showing as 1970 dates in the database.
    
    The issue is that some timestamps in the JSON data are stored as Unix timestamps
    (seconds since Jan 1, 1970) but displayed as string dates without proper conversion.
    This script will update those fields in the database.
    """
    logger.info("Starting timestamp fix script")
    
    try:
        # Connect to database
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Find records with 1970 timestamps
        logger.info("Finding records with 1970 timestamps...")
        query = """
            SELECT id, endpoint, timestamp, data 
            FROM hyblock_data 
            WHERE data::text LIKE '%1970%'
        """
        
        records = execute_query(conn, query)
        
        if not records:
            logger.info("No records with 1970 timestamps found")
            return True
        
        logger.info(f"Found {len(records)} records with 1970 timestamps")
        
        # Process and update each record
        updated_count = 0
        for record_id, endpoint, record_timestamp, data_dict in records:
            try:
                # Skip if no data array
                if not isinstance(data_dict, dict) or "data" not in data_dict:
                    continue
                
                # Flag to track if any changes were made
                changed = False
                
                # Update each data point in the array
                for i, item in enumerate(data_dict["data"]):
                    # Check if item has a timestamp that's in 1970 format
                    if "timestamp" in item and isinstance(item["timestamp"], str) and "1970-01-20" in item["timestamp"]:
                        # Check if there's an "openDate" numeric field to use for conversion
                        if "openDate" in item and isinstance(item["openDate"], (int, float)):
                            # Store the original string timestamp
                            item["original_timestamp"] = item["timestamp"]
                            
                            # Convert numeric timestamp to datetime
                            # Check if it's in milliseconds or seconds based on digits
                            if len(str(int(item["openDate"]))) > 10:
                                # Milliseconds
                                item["timestamp"] = pd.to_datetime(item["openDate"], unit='ms').isoformat()
                            else:
                                # Seconds
                                item["timestamp"] = pd.to_datetime(item["openDate"], unit='s').isoformat()
                                
                            changed = True
                            
                # Only update the database if changes were made
                if changed:
                    # Update the record in the database
                    update_query = """
                        UPDATE hyblock_data
                        SET data = %s
                        WHERE id = %s
                    """
                    
                    # Convert the modified data back to JSON string for the database
                    updated_json = json.dumps(data_dict)
                    
                    # Execute the update
                    success = execute_query(conn, update_query, params=[updated_json, record_id], fetch=False)
                    
                    if success:
                        updated_count += 1
                        logger.info(f"Updated record {record_id}")
                    else:
                        logger.error(f"Failed to update record {record_id}")
                        
            except Exception as e:
                logger.error(f"Error processing record {record_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        conn.close()
        logger.info(f"Successfully updated {updated_count} records out of {len(records)}")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing timestamps: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    fix_unix_timestamps() 