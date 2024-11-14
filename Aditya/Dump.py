def load_trained_model(self):
        try:
            vector_store_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'vector_store')
            if not os.path.exists(vector_store_path):
                raise FileNotFoundError("Trained model not found. Please run the training process first.")
            self.vector_store = FAISS.load_local(vector_store_path)
            print("Vector store loaded successfully!")
        except FileNotFoundError as e:
            print(e)
            raise  # Re-raise to trigger training in ModelTrigger
        except Exception as e:
            print(f"Error loading vector store: {e}")
            raise
