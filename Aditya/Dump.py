import os
from pgdb.db_setup import create_vector_table
from pgdb.vector_insertion import insert_csv_into_vector_table

if __name__ == "__main__":
    # Set environment variables
    os.environ['OPENAI_API_KEY'] = "your_openai_api_key"
    os.environ['DB_HOST'] = "localhost"
    os.environ['DB_PORT'] = "5432"
    os.environ['DB_NAME'] = "postgres"
    os.environ['DB_USER'] = "postgres"
    os.environ['DB_PASSWORD'] = "password"

    # Create the database table
    create_vector_table()

    # Path to the CSV file
    csv_file_path = "app/dataSource/azuresecuritybenchmarks.csv"

    # Insert data from CSV into the vector table
    insert_csv_into_vector_table(csv_file_path)
