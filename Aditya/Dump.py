# pgdb/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create pgvector extension
def init_vector():
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()

# pgdb/models.py
from sqlalchemy import Column, Integer, String, Float
from pgvector.sqlalchemy import Vector
from .db import Base

class SecurityBenchmark(Base):
    __tablename__ = "security_benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    control_domain = Column(String)
    asb_control_id = Column(String)
    asb_control_title = Column(String)
    guidance = Column(String)
    responsibility = Column(String)
    feature_name = Column(String)
    feature_description = Column(String)
    embedding = Column(Vector(1536))  # OpenAI embeddings dimension

# pgdb/embedding_utils.py
import openai
import os
from typing import List
import numpy as np
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def get_embedding(text: str) -> List[float]:
    """
    Get OpenAI embeddings for input text
    """
    text = text.replace("\n", " ")
    try:
        response = openai.Embedding.create(
            input=[text],
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def prepare_text_for_embedding(benchmark: dict) -> str:
    """
    Combine relevant fields for embedding
    """
    return f"{benchmark['service_name']} {benchmark['control_domain']} {benchmark['asb_control_title']} {benchmark['guidance']}"

# pgdb/vector_operations.py
import pandas as pd
from sqlalchemy.orm import Session
from typing import List, Dict
from .models import SecurityBenchmark
from .embedding_utils import get_embedding, prepare_text_for_embedding

def create_benchmark_with_embedding(db: Session, benchmark_data: dict) -> SecurityBenchmark:
    """
    Create a new security benchmark with embedding
    """
    # Prepare text and get embedding
    text = prepare_text_for_embedding(benchmark_data)
    embedding = get_embedding(text)
    
    # Create benchmark object
    db_benchmark = SecurityBenchmark(
        service_name=benchmark_data['service_name'],
        control_domain=benchmark_data['control_domain'],
        asb_control_id=benchmark_data['asb_control_id'],
        asb_control_title=benchmark_data['asb_control_title'],
        guidance=benchmark_data['guidance'],
        responsibility=benchmark_data['responsibility'],
        feature_name=benchmark_data['feature_name'],
        feature_description=benchmark_data['feature_description'],
        embedding=embedding
    )
    
    return db_benchmark

def batch_create_benchmarks(db: Session, csv_path: str, batch_size: int = 100) -> None:
    """
    Batch create benchmarks from CSV file
    """
    df = pd.read_csv(csv_path)
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        benchmarks = []
        
        for _, row in batch.iterrows():
            benchmark_data = row.to_dict()
            db_benchmark = create_benchmark_with_embedding(db, benchmark_data)
            benchmarks.append(db_benchmark)
        
        db.bulk_save_objects(benchmarks)
        db.commit()

def search_similar_benchmarks(db: Session, query: str, limit: int = 5) -> List[SecurityBenchmark]:
    """
    Search for similar benchmarks using vector similarity
    """
    query_embedding = get_embedding(query)
    
    if query_embedding is None:
        return []
    
    results = db.query(SecurityBenchmark).order_by(
        SecurityBenchmark.embedding.cosine_distance(query_embedding)
    ).limit(limit).all()
    
    return results

# pgdb/__init__.py
from .db import engine, get_db, init_vector, Base
from .models import SecurityBenchmark
from .vector_operations import (
    create_benchmark_with_embedding,
    batch_create_benchmarks,
    search_similar_benchmarks
)

__all__ = [
    'engine',
    'get_db',
    'init_vector',
    'Base',
    'SecurityBenchmark',
    'create_benchmark_with_embedding',
    'batch_create_benchmarks',
    'search_similar_benchmarks'
    ]
