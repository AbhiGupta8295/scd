# pgdb/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

DATABASE_URL = "postgresql://user:password@postgres:5432/vector_db"

# Create engine
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
    service_name = Column(String, index=True)
    control_domain = Column(String)
    asb_control_id = Column(String)
    asb_control_title = Column(String)
    guidance = Column(String)
    responsibility = Column(String)
    feature_name = Column(String)
    feature_description = Column(String)
    embedding = Column(Vector(1536))

# pgdb/vector_setup.py
import pandas as pd
import openai
from .db import engine, SessionLocal
from .models import Base, SecurityBenchmark

def setup_vector_db():
    """Initialize vector extension and create tables"""
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
    Base.metadata.create_all(bind=engine)

def get_embedding(text: str) -> list:
    """Get OpenAI embedding for text"""
    response = openai.Embedding.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

def load_csv_to_vector_db(csv_path: str):
    """Load CSV data into vector database"""
    df = pd.read_csv(csv_path)
    db = SessionLocal()
    
    try:
        for _, row in df.iterrows():
            # Create embedding from combined text
            text = f"{row['Service Name']} {row['Control Domain']} {row['ASB Control Title']} {row['Guidance']}"
            embedding = get_embedding(text)
            
            # Create database entry
            benchmark = SecurityBenchmark(
                service_name=row['Service Name'],
                control_domain=row['Control Domain'],
                asb_control_id=row['ASB Control ID'],
                asb_control_title=row['ASB Control Title'],
                guidance=row['Guidance'],
                responsibility=row['Responsibility'],
                feature_name=row['Feature Name'],
                feature_description=row['Feature Description'],
                embedding=embedding
            )
            db.add(benchmark)
        
        db.commit()
    finally:
        db.close()

# pgdb/__init__.py
from .vector_setup import setup_vector_db, load_csv_to_vector_db
from .db import get_db, engine
from .models import SecurityBenchmark

__all__ = ['setup_vector_db', 'load_csv_to_vector_db', 'get_db', 'engine', 'SecurityBenchmark']
