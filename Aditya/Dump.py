from embeddings import generate_embedding
from models import insert_data
from utils import read_csv

def process_csv(file_path):
    """
    Process the CSV, generate embeddings, and insert into the database.
    """
    data = read_csv(file_path)
    for service_name, control_domain in data:
        text = f"{service_name}, {control_domain}"
        embedding = generate_embedding(text)
        if embedding:
            insert_data(service_name, control_domain, embedding)
