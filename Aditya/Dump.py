import csv
from loguru import logger

def read_csv(file_path):
    """
    Read the CSV file and return the data.
    """
    data = []
    try:
        with open(file_path, mode="r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data.append((row["Service Name"], row["Control Domain"]))
        logger.info(f"Read {len(data)} rows from CSV.")
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
    return data
