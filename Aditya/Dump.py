import json
import random
import re
import os
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
        self.model = ChatOpenAI(api_key=self.config.get_openai_api_key(), temperature=0.2)
        self.model2 = OpenAI(api_key=self.config.get_openai_api_key())
        self.model_trainer = ModelTrainer()
        self.io_handler = IOHandler()

        try:
            self.vector_store = self.model_trainer.get_vector_store()
        except Exception as e:
            print(f"Error Loading Vector Store: {str(e)}")
            self.vector_store = None

        self.scd_templates = self.load_template()
        self.scd_template_azure = self.load_azure_template()
        self.scd_template_edj = self.load_azure_edj_template()

    def load_template(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(current_dir, 'templates', 'scdTemplate.json')
            with open(template_path, 'r') as f:
                return json.load(f).get('data', [])
        except Exception as e:
            print(f"Error loading template: {e}")
            return []

    def load_azure_template(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            temp_path = os.path.join(current_dir, 'templates', 'devsecops-scd.json')
            with open(temp_path, 'r') as f:
                return json.load(f).get('Azure_SCD_template', [])
        except Exception as e:
            print(f"Error loading Azure SCD template: {e}")
            return []

    def load_azure_edj_template(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            temp_path = os.path.join(current_dir, 'templates', 'edjonesTemplate.json')
            with open(temp_path, 'r') as f:
                return json.load(f).get('edj_scd_template', [])
        except Exception as e:
            print(f"Error loading EDJ SCD template: {e}")
            return []

    def generate_scd(self, user_prompt, service, additional_controls, azure_controls, benchmark_controls):
        if self.vector_store is None:
            raise ValueError("Vector store is not initialized. Please check vector store loading in ModelTrainer.")

        resource_name_match = re.search(r'\b(Azure\s\w+|AWS\s\w+|GCP\s\w+)\b', user_prompt, re.IGNORECASE)
        resource_name = resource_name_match.group(0) if resource_name_match else "GeneralService"

        relevant_controls = self.vector_store.similarity_search(user_prompt, k=25)

        vector_store_controls = []
        for doc in relevant_controls:
            control_id = doc.metadata.get('control_id') if hasattr(doc, 'metadata') else None
            if control_id:
                vector_store_controls.append({
                    'control_id': control_id,
                    'description': doc.page_content
                })

        # Ensure unique selection of templates for SCD generation
        selected_templates = random.sample(self.scd_templates, min(20, len(self.scd_templates)))

        scd_list = []
        
        for template in selected_templates:
            template_str = self.format_template(template, resource_name)
            
            prompt_template = PromptTemplate(
                input_variables=["control_descriptions", "user_prompt", "service", "control_ids", "scd_template", "additional_controls", "azure_controls"],
                template=(
                    "You are a cloud security expert. Based on the following control descriptions and the user's request, "
                    "generate between 17 to 20 detailed Security Control Definitions (SCDs) for the service: {service}. "
                    "User request: {user_prompt}. "
                    "IMPORTANT: You MUST use the following control IDs from our vector store. These are the only valid control IDs you should use: {vector_store_controls}. "
                    "Control descriptions from our knowledge base: {control_descriptions}. "
                    "Requirements: 1. Generate EXACTLY 17-20 SCDs this is mandatory. 2. Use ONLY the control IDs provided above from the vector dataset."
                )
            )

            control_descriptions = "\n".join([doc['description'] for doc in vector_store_controls])
            control_ids_info = "\n".join([f"- {ctrl['control_id']}" for ctrl in vector_store_controls])

            response_chain = prompt_template | self.model | StrOutputParser()
            
            response = response_chain.invoke({
                "control_descriptions": control_descriptions,
                "user_prompt": user_prompt,
                "service": service,
                "vector_store_controls": control_ids_info,
                "scd_template": template_str,
                "additional_controls": ", ".join(additional_controls),
                "azure_controls": ", ".join(azure_controls)
            })

            validated_scds = self.validate_scds(response)

            # If we don't get enough SCDs, try one more time with a stronger emphasis
            if len(validated_scds) < 17:
                retry_prompt = f"{user_prompt} IMPORTANT: You MUST generate at least 17 SCDs. Current generation only produced {len(validated_scds)}."
                
                response_retry = response_chain.invoke({
                    "control_descriptions": control_descriptions,
                    "user_prompt": retry_prompt,
                    "service": service,
                    "vector_store_controls": control_ids_info,
                    "scd_template": template_str,
                    "additional_controls": ", ".join(additional_controls),
                    "azure_controls": ", ".join(azure_controls)
                })
                
                validated_scds += self.validate_scds(response_retry)

            # Add validated SCDs to the list ensuring uniqueness
            for scd in validated_scds:
                if scd not in scd_list:
                    scd_list.append(scd)

        # Check if we have enough unique SCDs generated
        if len(scd_list) < 17:
            raise ValueError("Not enough unique SCDs generated. Please adjust your templates or controls.")

        return "\n\n".join(scd_list)

    def validate_scds(self, response):
        scd_pattern = re.compile(r'Control ID:.*?(?=Control ID:|$)', re.DOTALL)
        scds = scd_pattern.findall(response)
        
        validated_scds = []
        
        required_fields = [
            'Control ID:', 
            'Control Domain:', 
            'Control Title:', 
            'Mapping to NIST CSF v1.1 control:', 
            'Client Requirement if Any:', 
            'Policy Name:', 
            'Policy Description:', 
            'Implementation Details:', 
            'Responsibility:', 
            'Frequency:', 
            'Evidence:'
        ]

        for scd in scds:
            if all(field in scd for field in required_fields):
                validated_scds.append(scd.strip())

        return validated_scds

    def format_template(self, template, resource_name):
        if isinstance(template, dict):
            control_id = template.get("control_id") or f"{resource_name}_default"
            
            formatted = f"Control ID: {control_id}\n"
            formatted += f"Control Domain: {template.get('control_domain', 'N/A')}\n"
            formatted += f"Control Title: {template.get('control_title', 'N/A')}\n"
            formatted += f"Mapping to NIST CSF v1.1 control: {template.get('mapping_to_NIST_CSF_v1.1_control', 'N/A')}\n"
            formatted += f"Client Requirement if Any: {template.get('client_requirement_if_any', 'N/A')}\n"
            formatted += f"Policy Name: {template.get('policy_name', 'N/A')}\n"
            formatted += f"Policy Description: {template.get('policy_description', 'N/A')}\n"
            
            formatted += "Implementation Details:\n"
            
            for detail in template.get("implementation_details", []):
                formatted += f" || {detail}\n"
            
            formatted += f"Responsibility: {template.get('responsibility', 'N/A')}\n"
            
            formatted += f"Evidence: {template.get('evidence', 'N/A')}"
            
            return formatted
        
        return ""
