import re
import os
import json
import random
from openai import OpenAI
from src.utils.config import Config
from langchain_openai import ChatOpenAI
from src.data.io_handler import IOHandler
from langchain.prompts import PromptTemplate
from src.model.model_trainer import ModelTrainer
from langchain_core.output_parsers import StrOutputParser

class AIModel:
    def __init__(self):
        self.config = Config()
        self.model = ChatOpenAI(
            api_key=self.config.get_openai_api_key(),
            temperature=0.3,
            model="gpt-4-0"
        )
        self.model2 = OpenAI(api_key=self.config.get_openai_api_key())
        self.model_trainer = ModelTrainer()
        self.io_handler = IOHandler()
        self.vector_store = None
        self.debug_mode = True  # Enable debug mode
        self.initialize_vector_store()
        self.initialize_templates()

    def initialize_vector_store(self):
        try:
            self.vector_store = self.model_trainer.get_vector_store()
            if self.debug_mode:
                print(f"Vector store initialized: {type(self.vector_store)}")
                # Print first few documents to verify content
                sample_docs = self.vector_store.similarity_search("test", k=1)
                print(f"Sample document from vector store: {sample_docs[0].page_content if sample_docs else 'No documents found'}")
        except Exception as e:
            print(f"Error Loading Vector Store: {str(e)}")
            raise

    def get_relevant_controls(self, user_prompt, k=25):
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        if self.debug_mode:
            print(f"Searching vector store with prompt: {user_prompt}")
        
        try:
            controls = self.vector_store.similarity_search(user_prompt, k=k)
            
            if self.debug_mode:
                print(f"Found {len(controls)} controls")
                if controls:
                    print("Sample control:", controls[0].page_content)
            
            if not controls:
                # Fallback search with broader terms
                broader_prompt = " ".join(user_prompt.split()[:3])  # Use first 3 words
                print(f"No controls found, trying broader search: {broader_prompt}")
                controls = self.vector_store.similarity_search(broader_prompt, k=k)
            
            return [{
                'control_id': doc.metadata.get('control_id') if hasattr(doc, 'metadata') else None,
                'description': doc.page_content
            } for doc in controls if hasattr(doc, 'metadata') and doc.metadata.get('control_id')]
        except Exception as e:
            print(f"Error in similarity search: {str(e)}")
            raise

    def generate_scd(self, user_prompt, service, additional_controls, azure_controls, benchmark_controls):
        try:
            # Get relevant controls from vector store
            vector_store_controls = self.get_relevant_controls(user_prompt)
            
            if not vector_store_controls:
                raise ValueError("No relevant controls found in vector store. Please check the vector store content and indexing.")
            
            if self.debug_mode:
                print(f"Found {len(vector_store_controls)} relevant controls")
                print("First control:", vector_store_controls[0] if vector_store_controls else "None")
            
            # Rest of the generate_scd method remains the same
            control_descriptions = [ctrl['description'] for ctrl in vector_store_controls]
            control_ids_info = "\n".join([f"- {ctrl['control_id']}" for ctrl in vector_store_controls])

            resource_name = self.get_resource_name(user_prompt)
            template_str = self.format_template(random.choice(self.scd_templates), resource_name)
            template_str2 = self.format_template(random.choice(self.scd_template_azure), resource_name)
            edj_temp = self.format_template(random.choice(self.scd_template_edj), resource_name)

            prompt_template = self.create_scd_prompt_template()
            chain = prompt_template | self.model | StrOutputParser()

            response = chain.invoke({
                "control_descriptions": "\n".join(control_descriptions),
                "user_prompt": user_prompt,
                "service": service,
                "vector_store_controls": control_ids_info,
                "scd_template": template_str,
                "additional_controls": ", ".join(additional_controls),
                "azure_controls": template_str2,
                "edj_temp": edj_temp,
                "benchmark_controls": benchmark_controls
            })

            validated_scds = self.validate_scds(response)
            if len(validated_scds) < 17:
                if self.debug_mode:
                    print(f"Warning: Only generated {len(validated_scds)} SCDs, retrying...")
                retry_prompt = f"{user_prompt} IMPORTANT: You MUST generate at least 17 SCDs. Current generation only produced {len(validated_scds)}."
                response = chain.invoke({
                    "control_descriptions": "\n".join(control_descriptions),
                    "user_prompt": retry_prompt,
                    "service": service,
                    "vector_store_controls": control_ids_info,
                    "scd_template": template_str,
                    "additional_controls": ", ".join(additional_controls),
                    "azure_controls": template_str2,
                    "edj_temp": edj_temp,
                    "benchmark_controls": benchmark_controls
                })
                validated_scds = self.validate_scds(response)

            return "\n\n".join(validated_scds)
        except Exception as e:
            print(f"Error in generate_scd: {str(e)}")
            raise

    # ... (rest of the methods remain the same)
