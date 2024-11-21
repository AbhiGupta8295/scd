import os
import csv
import openai
import psycopg2

def generate_embedding(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

def insert_csv_into_vector_table(csv_path):
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

    # Open the CSV file and iterate over rows
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Combine relevant columns for embeddings
            combined_text = f"{row['Service Name']}. {row['Guidance']}. {row['Feature Description']}"
            embedding = generate_embedding(combined_text)

            # Insert into the table
            cursor.execute("""
                INSERT INTO azure_security_benchmarks (
                    service_name,
                    control_title,
                    guidance,
                    responsibility,
                    feature_name,
                    feature_description,
                    embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row['Service Name'],
                row['ASB Control Title'],
                row['Guidance'],
                row['Responsibility'],
                row['Feature Name'],
                row['Feature Description'],
                embedding
            ))
            conn.commit()

    cursor.close()
    conn.close()
    print("Data successfully inserted into 'azure_security_benchmarks' table.")
