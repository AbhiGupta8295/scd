import os
import psycopg2

def create_vector_table():
    # Database connection details
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

    # Connect to the database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    # Create a table for vector embeddings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS azure_security_benchmarks (
            id SERIAL PRIMARY KEY,
            service_name TEXT,
            control_title TEXT,
            guidance TEXT,
            responsibility TEXT,
            feature_name TEXT,
            feature_description TEXT,
            embedding VECTOR(1536)  -- Adjust the dimension to OpenAI embedding size
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Table 'azure_security_benchmarks' created successfully.")
