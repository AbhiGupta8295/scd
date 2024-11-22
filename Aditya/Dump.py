# pgdb/init.py
import os
from dotenv import load_dotenv
from db_setup import init_db, load_benchmarks

def initialize_database():
    load_dotenv()
    
    # Get database connection details from environment variables
    db_params = {
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'vectordb')
    }
    
    connection_string = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    
    # Initialize database and create tables
    engine = init_db(connection_string)
    
    # Load benchmarks from CSV
    csv_path = '../dataSource/azuresecuritybenchmarks.csv'
    load_benchmarks(csv_path, engine)
    
    return engine

if __name__ == "__main__":
    initialize_database()
