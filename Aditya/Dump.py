import os
import pandas as pd

class ModelTrainer:
    def __init__(self, embeddings):
        self.embeddings = embeddings

    def train(self):
        print("Starting training process...")

        # Dynamically set data directory path based on the current file's location
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        data_dir = os.path.join(project_root, 'app', 'dataSource')
        print(f"Data directory: {data_dir}")

        # Check if data directory exists
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
            
            # Replace with actual embedding and model training logic
            # Example: self.embeddings = your_embedding_process(combined_data)
            
            self.save_trained_model()
            print("Model training completed and saved.")
        else:
            print("No data to train the model.")

    def load_trained_model(self):
        model_path = os.path.join(os.path.dirname(__file__), 'trained_model.pkl')
        if os.path.exists(model_path):
            print("Loading the trained model...")
            # Load model code here
        else:
            raise FileNotFoundError("Trained model not found.")

    def save_trained_model(self):
        model_path = os.path.join(os.path.dirname(__file__), 'trained_model.pkl')
        print(f"Saving trained model to {model_path}...")
        # Save model code here
