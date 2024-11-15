import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.model.model_trainer import ModelTrainer  # Import ModelTrainer directly

# Initialize the FastAPI app
app = FastAPI()

# Configure CORS middleware (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate ModelTrainer and handle loading or training
try:
    # Replace 'embeddings' with the actual embeddings object required by ModelTrainer
    model_trainer = ModelTrainer(embeddings)
    model_trainer.load_trained_model()  # Attempt to load the model
    print("Trained model loaded successfully.")
except FileNotFoundError:
    print("Trained model not found. Starting training process...")
    model_trainer.train()  # Train and save the model if not found
    print("Model training completed and saved.")
except Exception as e:
    print(f"Error during model loading or training: {e}")

# Include your FastAPI routers (if any)
# from src.fastapi.scdGenerate import router as scd_router
# app.include_router(scd_router)

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
