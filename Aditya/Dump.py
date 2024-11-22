import psycopg2
from loguru import logger
from config import Config

def get_db_connection():
    """Create a database connection."""
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def create_table():
    """Create the necessary table and enable pgvector."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;

                CREATE TABLE IF NOT EXISTS azure_security (
                    id SERIAL PRIMARY KEY,
                    service_name TEXT NOT NULL,
                    control_domain TEXT NOT NULL,
                    embedding VECTOR(1536),
                    UNIQUE (service_name, control_domain)
                );
            """)
            conn.commit()
            logger.info("Database table created.")
