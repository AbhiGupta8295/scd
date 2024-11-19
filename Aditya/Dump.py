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
        self.model = ChatOpenAI(api_key=self.config.get_openai_api_key(), temperature=0.3, model="gpt-4")
        self.model_trainer = ModelTrainer()
        self.io_handler = IOHandler()

        try:
            self.vector_store = self.model_trainer.get_vector_store()
        except Exception as e:
            print(f"Error Loading Vector Store: {str(e)}")
            self.vector_store = None

        # Load SCD templates
        self.scd_templates = self.load_template('scdTemplate.json', 'data')
        self.scd_template_azure = self.load_template('devsecops-scd.json', 'Azure_SCD_template')
        self.scd_template_edj = self.load_template('edjonesTemplate.json', 'edj_scd_template')

    def load_template(self, filename, key):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(current_dir, 'templates', filename)
            with open(template_path, 'r') as f:
                return json.load(f).get(key, [])
        except Exception as e:
            print(f"Error loading template {filename}: {e}")
            return []

    def generate_scd(self, user_prompt, service, additional_controls, azure_controls, benchmark_controls):
        if not self.vector_store:
            raise ValueError("Vector store is not initialized. Please check vector store loading in ModelTrainer.")

        # Extract resource name
        resource_name_match = re.search(r'\b(Azure\s\w+|AWS\s\w+|GCP\s\w+)\b', user_prompt, re.IGNORECASE)
        resource_name = resource_name_match.group(0) if resource_name_match else "GeneralService"

        # Search for relevant controls
        relevant_controls = self.vector_store.similarity_search(user_prompt, k=25)
        vector_store_controls = [
            {
                'control_id': doc.metadata.get('control_id'),
                'description': doc.page_content
            }
            for doc in relevant_controls if hasattr(doc, 'metadata') and 'control_id' in doc.metadata
        ]

        # Ensure at least 17 controls
        while len(vector_store_controls) < 17:
            vector_store_controls.append({
                'control_id': f"{resource_name}_{random.randint(1000, 9999)}",
                'description': "Generated control description."
            })

        # Format templates
        scd_template = self.format_template(random.choice(self.scd_templates), resource_name)
        azure_template = self.format_template(random.choice(self.scd_template_azure), resource_name)
        edj_template = self.format_template(random.choice(self.scd_template_edj), resource_name)

        # Prepare control descriptions and IDs
        control_descriptions = "\n".join([ctrl['description'] for ctrl in vector_store_controls])
        control_ids_info = "\n".join([f"- {ctrl['control_id']}" for ctrl in vector_store_controls])

        # Generate prompt
        prompt_template = PromptTemplate(
            input_variables=["control_descriptions", "user_prompt", "service", "control_ids", "scd_template"],
            template=(
                "You are a cloud security expert. Generate 17-20 detailed Security Control Definitions (SCDs) "
                "for the following cloud service based on the control descriptions, templates, and user's prompt.\n\n"
                "Control Descriptions:\n{control_descriptions}\n\n"
                "User Request: {user_prompt}\n\n"
                "Service: {service}\n\n"
                "Control IDs:\n{control_ids}\n\n"
                "SCD Template:\n{scd_template}\n"
            )
        )

        # Generate SCDs
        response = self.model.generate_text(
            prompt_template.format(
                control_descriptions=control_descriptions,
                user_prompt=user_prompt,
                service=service,
                control_ids=control_ids_info,
                scd_template=scd_template
            )
        )
        validated_scds = self.validate_scds(response)

        # Retry if necessary
        if len(validated_scds) < 17:
            retry_prompt = f"{user_prompt} Ensure to generate at least 17 detailed SCDs."
            response = self.model.generate_text(
                prompt_template.format(
                    control_descriptions=control_descriptions,
                    user_prompt=retry_prompt,
                    service=service,
                    control_ids=control_ids_info,
                    scd_template=scd_template
                )
            )
            validated_scds = self.validate_scds(response)

        return "\n\n".join(validated_scds)

    def validate_scds(self, response):
        scd_pattern = re.compile(r'Control ID:.*?(?=Control ID:|$)', re.DOTALL)
        scds = scd_pattern.findall(response)

        validated_scds = []
        required_fields = [
            'Control ID:', 'Control Domain:', 'Control Title:',
            'Mapping to NIST CSF v1.1 control:', 'Policy Name:', 'Policy Description:',
            'Implementation Details:', 'Responsibility:', 'Frequency:', 'Evidence:'
        ]

        for scd in scds:
            if all(field in scd for field in required_fields):
                validated_scds.append(scd.strip())

        return validated_scds

    def format_template(self, template, resource_name):
        if isinstance(template, dict):
            return json.dumps(template).replace("{resource_name}", resource_name)
        return template
