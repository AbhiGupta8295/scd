# pgdb/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

DATABASE_URL = "postgresql://user:password@postgres:5432/vector_db"

# Create a database engine
engine = create_engine(DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# pgdb/models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class SecurityBenchmark(Base):
    __tablename__ = "security_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String)
    control_domain = Column(String)
    asb_control_id = Column(String)
    asb_control_title = Column(String)
    guidance = Column(String)
    responsibility = Column(String)
    feature_name = Column(String)
    feature_description = Column(String)
    embedding = Column(Vector(1536))

# pgdb/embeddings.py
import openai
from typing import List, Optional

class EmbeddingGenerator:
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            openai.api_key = api_key

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        text = text.replace("\n", " ")
        response = openai.Embedding.create(input=[text], model=model)
        return response['data'][0]['embedding']

    def generate_benchmark_embedding(self, benchmark_data: dict) -> List[float]:
        """Generate embedding for security benchmark data"""
        combined_text = f"{benchmark_data['service_name']} {benchmark_data['control_domain']} "\
                       f"{benchmark_data['asb_control_title']} {benchmark_data['guidance']}"
        return self.get_embedding(combined_text)

# pgdb/__init__.py
from .db import get_db, engine
from .models import Base, SecurityBenchmark
from .embeddings import EmbeddingGenerator

__all__ = ['get_db', 'engine', 'Base', 'SecurityBenchmark', 'EmbeddingGenerator']
