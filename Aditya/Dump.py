import os
from io_handler import IOHandler  # Assuming IOHandler is the utility for loading CSV data
from faiss import FAISS  # Assuming FAISS import is correct

class ModelTrainer:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.vector_store = None

    def train(self):
        try:
            print("Starting training process...")

            # Step 1: Verify data directory path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
            data_dir = os.path.join(project_root, 'dataSource')
            print(f"Data directory: {data_dir}")

            if not os.path.exists(data_dir):
                raise FileNotFoundError(f"Data directory not found at {data_dir}")

            # Step 2: Find CSV files in the data directory
            csv_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
            print(f"Found CSV files: {csv_files}")

            if not csv_files:
                raise FileNotFoundError("No CSV files found in data source directory.")

            # Step 3: Load data from CSV files
            combined_data = IOHandler.load_csv(csv_files)
            if combined_data is None or combined_data.empty:
                raise ValueError("Loaded data is empty after combining CSV files.")

            print("Data loaded successfully for training.")

            # Step 4: Prepare data for vector storage
            texts = combined_data.apply(lambda row: ' '.join(row.values.astype(str)), axis=1).tolist()
            metadatas = combined_data.to_dict('records')

            # Ensure metadata is in the correct format
            for metadata in metadatas:
                for key, value in metadata.items():
                    metadata[key] = str(value)

            print("Data prepared for vector store creation.")

            # Step 5: Create vector store
            self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
            print("Vector store created in memory.")

            # Step 6: Save the vector store
            vector_store_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'vector_store')
            os.makedirs(vector_store_path, exist_ok=True)
            print(f"Vector store directory ensured at: {vector_store_path}")

            self.vector_store.save_local(vector_store_path)
            print("Vector store saved successfully at:", vector_store_path)

        except Exception as e:
            print(f"Error during training: {e}")
