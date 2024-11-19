import re
import os
import json
import random
from typing import List, Dict, Any
from openai import OpenAI
from src.utils.config import Config
from langchain_openai import ChatOpenAI
from src.data.io_handler import IOHandler
from langchain.prompts import PromptTemplate
from src.model.model_trainer import ModelTrainer
from langchain.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain.embeddings import OpenAIEmbeddings

class AIModel:
    def __init__(self):
        self.config = Config()
        self.model = ChatOpenAI(
            api_key=self.config.get_openai_api_key(),
            temperature=0.3,
            model="gpt-4-0"
        )
        self.model2 = OpenAI(api_key=self.config.get_openai_api_key())
        self.embeddings = OpenAIEmbeddings(api_key=self.config.get_openai_api_key())
        self.model_trainer = ModelTrainer()
        self.io_handler = IOHandler()
        self.vector_store = None
        self.initialize_vector_store()
        self.initialize_templates()

    def initialize_vector_store(self) -> None:
        try:
            # First try loading from model trainer
            self.vector_store = self.model_trainer.get_vector_store()
            
            # Fallback: If vector store is empty, initialize with default controls
            if not self.vector_store or not self._test_vector_store():
                print("Initializing vector store with default controls...")
                self._initialize_default_controls()
                
        except Exception as e:
            print(f"Error in vector store initialization: {str(e)}")
            # Fallback to default controls
            self._initialize_default_controls()

    def _test_vector_store(self) -> bool:
        """Test if vector store has content"""
        try:
            test_results = self.vector_store.similarity_search("security", k=1)
            return len(test_results) > 0
        except:
            return False

    def _initialize_default_controls(self) -> None:
        """Initialize vector store with default security controls"""
        default_controls = [
            {"id": "SEC-001", "content": "Access Control Policy"},
            {"id": "SEC-002", "content": "Authentication Mechanisms"},
            {"id": "SEC-003", "content": "Data Encryption Standards"},
            # Add more default controls as needed
        ]
        
        texts = [ctrl["content"] for ctrl in default_controls]
        metadatas = [{"control_id": ctrl["id"]} for ctrl in default_controls]
        
        self.vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas
        )

    def get_relevant_controls(self, user_prompt: str, k: int = 25) -> List[Dict[str, str]]:
        """Get relevant security controls with multiple fallback mechanisms"""
        if not self.vector_store:
            self._initialize_default_controls()

        all_controls = []
        seen_control_ids = set()

        # Try multiple search strategies
        search_strategies = [
            user_prompt,
            f"security controls for {user_prompt}",
            "basic security controls",
            "common security requirements"
        ]

        for strategy in search_strategies:
            try:
                results = self.vector_store.similarity_search(strategy, k=k)
                
                for doc in results:
                    if not hasattr(doc, 'metadata') or 'control_id' not in doc.metadata:
                        continue
                    
                    control_id = doc.metadata['control_id']
                    if control_id not in seen_control_ids:
                        seen_control_ids.add(control_id)
                        all_controls.append({
                            'control_id': control_id,
                            'description': doc.page_content
                        })
                
                if len(all_controls) >= 5:  # If we have enough controls, break
                    break
                    
            except Exception as e:
                print(f"Search failed for strategy '{strategy}': {str(e)}")
                continue

        # If still no controls found, use default controls
        if not all_controls:
            all_controls = [
                {
                    'control_id': 'SEC-001',
                    'description': 'Basic Access Control Policy for cloud resources'
                },
                {
                    'control_id': 'SEC-002',
                    'description': 'Authentication and Authorization Requirements'
                },
                {
                    'control_id': 'SEC-003',
                    'description': 'Data Protection and Encryption Standards'
                }
                # Add more default controls as needed
            ]

        return all_controls[:k]

    # ... rest of the AIModel class methods remain the same ...
