import os
import pandas as pd

class ModelTrainer:
    def __init__(self, embeddings, vector_store_path='vector_store.pkl'):
        self.embeddings = embeddings
        self.vector_store_path = os.path.join(os.path.dirname(__file__), vector_store_path)

    def train(self):
        print("Starting training process...")

        # Dynamically set the correct data directory path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        data_dir = os.path.join(project_root, 'dataSource')
        print(f"Data directory: {data_dir}")

        # Verify if data directory exists
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found at {data_dir}")

        # Find CSV files in the data directory
        csv_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
        print(f"Found CSV files: {csv_files}")

        if not csv_files:
            print("No CSV files found in the data directory.")
            return

        # Process each CSV file
        data_frames = []
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                data_frames.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")
                continue

        # Combine data if there are multiple CSV files
        if data_frames:
            combined_data = pd.concat(data_frames, ignore_index=True)
            print("Combined data for training loaded.")
            
            # Placeholder for embedding and model training logic
            # Example: self.embeddings = your_embedding_process(combined_data)
            
            if self.save_trained_model():
                print("Model training completed and saved.")
            else:
                print("Error: Failed to save trained model.")
        else:
            print("No data to train the model.")

    def load_trained_model(self):
        if os.path.exists(self.vector_store_path):
            print("Loading the trained model from vector store...")
            # Load model code here
            # Example: with open(self.vector_store_path, 'rb') as file: self.model = pickle.load(file)
        else:
            raise FileNotFoundError("Trained model not found. Please run the training process first.")

    def save_trained_model(self):
        print(f"Saving trained model to {self.vector_store_path}...")

        try:
            # Save model code here
            # e.g., with open(self.vector_store_path, 'wb') as file: pickle.dump(self.embeddings, file)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
