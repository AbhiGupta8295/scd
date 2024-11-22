from database import get_db_connection
from loguru import logger

def insert_data(service_name, control_domain, embedding):
    """
    Insert data into the database.
    Avoid duplicates with ON CONFLICT.
    """
    query = """
        INSERT INTO azure_security (service_name, control_domain, embedding)
        VALUES (%s, %s, %s)
        ON CONFLICT (service_name, control_domain) DO NOTHING;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(query, (service_name, control_domain, embedding))
                conn.commit()
                logger.info(f"Inserted/Skipped: {service_name}, {control_domain}")
            except Exception as e:
                logger.error(f"Error inserting data: {e}")
