def train(self):
    try:
        print("Training process started...")  # Debug statement

        # Set up data directory and check its existence
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        data_dir = os.path.join(project_root, 'dataSource')
        print(f"Data directory path: {data_dir}")  # Debug statement

        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"The data source directory does not exist: {data_dir}")

        # Load CSV files
        csv_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in the data source directory: {data_dir}")

        combined_data = IOHandler.load_csv(csv_files)
        if combined_data is None or combined_data.empty:
            raise ValueError("No data available for training after loading CSV files.")

        # Prepare data for vector storage
        texts = combined_data.apply(lambda row: ' '.join(row.values.astype(str)), axis=1).tolist()
        metadatas = combined_data.to_dict('records')

        for metadata in metadatas:
            for key, value in metadata.items():
                metadata[key] = str(value)

        # Create and save the vector store
        self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        vector_store_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'vector_store')
        os.makedirs(vector_store_path, exist_ok=True)
        print(f"Vector store path: {vector_store_path}")  # Debug statement

        self.vector_store.save_local(vector_store_path)
        print("Model trained and saved successfully!")

    except Exception as e:
        print(f"Error training model: {e}")
