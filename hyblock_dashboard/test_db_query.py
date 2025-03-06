import os
import sys
import psycopg2
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hyblock')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

def connect_to_db():
    """Connect to the PostgreSQL database server"""
    conn = None
    try:
        # Connect to the PostgreSQL server
        print(f"Connecting to database {DB_NAME} on {DB_HOST}:{DB_PORT} as {DB_USER}")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error connecting to database: {error}")
        sys.exit(1)

def check_tables(conn):
    """Check the tables in the database"""
    try:
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check if market_data table exists and has data
        if any(table[0] == 'market_data' for table in tables):
            cursor.execute("SELECT COUNT(*) FROM market_data")
            count = cursor.fetchone()[0]
            print(f"\nmarket_data table has {count} rows")
            
            if count > 0:
                cursor.execute("""
                    SELECT coin, exchange, timeframe, data_type, created_at
                    FROM market_data
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                recent_data = cursor.fetchall()
                print("\nMost recent market_data entries:")
                for row in recent_data:
                    print(f"Coin: {row[0]}, Exchange: {row[1]}, Timeframe: {row[2]}, Type: {row[3]}, Time: {row[4]}")
        
        # Check if funding_rates table exists and has data
        if any(table[0] == 'funding_rates' for table in tables):
            cursor.execute("SELECT COUNT(*) FROM funding_rates")
            count = cursor.fetchone()[0]
            print(f"\nfunding_rates table has {count} rows")
            
            if count > 0:
                cursor.execute("""
                    SELECT coin, exchange, rate, timestamp
                    FROM funding_rates
                    ORDER BY timestamp DESC
                    LIMIT 5
                """)
                recent_data = cursor.fetchall()
                print("\nMost recent funding_rates entries:")
                for row in recent_data:
                    print(f"Coin: {row[0]}, Exchange: {row[1]}, Rate: {row[2]}, Time: {row[3]}")
        
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error querying database: {error}")

def main():
    """Main function to test database connection and query data"""
    conn = connect_to_db()
    if conn is not None:
        print("Database connection successful!")
        check_tables(conn)
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main() 