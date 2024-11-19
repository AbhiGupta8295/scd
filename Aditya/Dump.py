import re
import os
import json
import random
from openai import OpenAI as OpenAIModel  # Fixing OpenAI import name
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
            model="gpt-4"
        )
        self.model_trainer = ModelTrainer()
        self.io_handler = IOHandler()
        self.vector_store = None
        self.initialize_vector_store()
        self.initialize_templates()

    def initialize_vector_store(self):
        try:
            self.vector_store = self.model_trainer.get_vector_store()
        except Exception as e:
            print(f"Error Loading Vector Store: {str(e)}")

    def initialize_templates(self):
        self.scd_templates = self.load_template()
        self.scd_template_azure = self.load_azure_template()
        self.scd_template_edj = self.load_azure_edj_template()

    def load_template(self):
        return self._load_json_template('scdTemplate.json', 'data')

    def load_azure_template(self):
        return self._load_json_template('devsecops-scd.json', 'Azure_SCD_template')

    def load_azure_edj_template(self):
        return self._load_json_template('edjonesTemplate.json', 'edj_scd_template')

    def _load_json_template(self, filename, key):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(current_dir, 'templates', filename)
            with open(template_path, 'r') as f:
                return json.load(f).get(key, [])
        except Exception as e:
            print(f"Error loading template {filename}: {e}")
            return []

    def get_resource_name(self, user_prompt):
        resource_match = re.search(
            r'\b(Azure\s\w+|AWS\s\w+|GCP\s\w+)\b',
            user_prompt,
            re.IGNORECASE
        )
        return resource_match.group(0) if resource_match else "GeneralService"

    def get_relevant_controls(self, user_prompt, k=25):
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        controls = self.vector_store.similarity_search(user_prompt, k=k)
        return [{
            'control_id': doc.metadata.get('control_id') if hasattr(doc, 'metadata') else None,
            'description': doc.page_content
        } for doc in controls if hasattr(doc, 'metadata') and doc.metadata.get('control_id')]

    def generate_scd(self, user_prompt, service, additional_controls, azure_controls, benchmark_controls):
        try:
            # Get relevant controls from vector store
            vector_store_controls = self.get_relevant_controls(user_prompt)
            if not vector_store_controls:
                raise ValueError("No relevant controls found in vector store")
            
            # Prepare control information
            control_descriptions = [ctrl['description'] for ctrl in vector_store_controls]
            control_ids_info = "\n".join([f"- {ctrl['control_id']}" for ctrl in vector_store_controls])

            # Format templates
            resource_name = self.get_resource_name(user_prompt)
            template_str = self.format_template(random.choice(self.scd_templates), resource_name)
            azure_template = self.format_template(random.choice(self.scd_template_azure), resource_name)
            edj_temp = self.format_template(random.choice(self.scd_template_edj), resource_name)

            if not all([template_str, azure_template, edj_temp]):
                raise ValueError("Failed to format one or more templates")

            # Create prompt template
            prompt_template = self.create_scd_prompt_template()
            chain = prompt_template | self.model | StrOutputParser()

            # Prepare input parameters
            input_params = {
                "control_descriptions": "\n".join(control_descriptions),
                "user_prompt": user_prompt,
                "service": service,
                "vector_store_controls": control_ids_info,
                "scd_template": template_str,
                "additional_controls": ", ".join(additional_controls or []),
                "azure_controls": azure_template,
                "edj_temp": edj_temp,
                "benchmark_controls": benchmark_controls or ""
            }

            # Generate initial response
            response = chain.invoke(input_params)
            if not response:
                raise ValueError("No response generated from the model")

            # Validate and potentially retry
            validated_scds = self.validate_scds(response)
            if not validated_scds:
                raise ValueError("No valid SCDs found in response")

            if len(validated_scds) < 17:
                # Retry with stronger emphasis
                retry_prompt = f"{user_prompt} IMPORTANT: You MUST generate at least 17 SCDs. Current generation only produced {len(validated_scds)}."
                input_params["user_prompt"] = retry_prompt
                
                response = chain.invoke(input_params)
                if not response:
                    raise ValueError("No response generated from retry attempt")
                
                validated_scds = self.validate_scds(response)
                if not validated_scds:
                    raise ValueError("No valid SCDs found in retry response")

            # Join validated SCDs with double newlines
            result = "\n\n".join(validated_scds)
            if not result:
                raise ValueError("Failed to join validated SCDs")

            return result

        except Exception as e:
            print(f"Error in generate_scd: {str(e)}")
            # Return a fallback response instead of None
            return f"Error generating SCDs: {str(e)}"

    def create_scd_prompt_template(self):
        template = """
        You are a cloud security expert. Based on the following control descriptions and the user's request, generate between 17 to 20 detailed Security Control Definitions (SCDs).

        IMPORTANT: You MUST use the following control IDs from our vector store. These are the only valid control IDs you should use: {vector_store_controls}

        IMPORTANT RULES:
        1. DO NOT include service names or cloud provider names in Control IDs
        2. Use ONLY the control IDs from the provided vector store controls for the mentioned cloud service in the {user_prompt}
        3. Always map controls to NIST CSF v1.1 when available in the vector store data

        Control descriptions from our knowledge base:
        {control_descriptions}

        Based on these descriptions and the following user request, generate detailed Security Control Definitions (SCDs) for the service: {service}

        User request: {user_prompt}
        Service: {service}

        Requirements:
        1. Generate EXACTLY 17-20 SCDs (this is mandatory)
        2. Use ONLY the control IDs provided above from the vector dataset
        3. Each SCD must follow this exact format:

        Control ID: [Use control ID from vector store]
        Control Domain: [Domain name from benchmark]
        Control Title: [Security benchmark control title]
        Mapping to NIST CSF v1.1 control: [Mapped NIST control]
        Client Requirement if Any: [X or blank]
        Policy Name: [Feature name from benchmark]
        Policy Description: [Brief description]
        Implementation Details: [Detailed implementation steps]
        Responsibility: [Based on benchmark]
        Frequency: [Continuous/Annual Review/Quarterly]
        Evidence: [Required compliance evidence]

        Reference templates:
        {edj_temp}
        {template_str2}

        Azure-specific controls (if applicable):
        {benchmark_controls}

        Additional control areas to address:
        {additional_controls}

        FINAL CHECK:
        - Ensure you've created at least 17 SCDs
        - Verify each SCD uses a valid control ID from the provided list
        - Confirm all required sections are present in each SCD
        - Ensure SCDs are related to the cloud service mentioned in the {user_prompt}
        """
        return PromptTemplate(
            input_variables=[
                "control_descriptions", "user_prompt", "service",
                "vector_store_controls", "scd_template", "additional_controls",
                "azure_controls", "edj_temp", "benchmark_controls"
            ],
            template=template
        )

    def validate_scds(self, response):
        scd_pattern = re.compile(r'Control ID:.*?(?=Control ID:|$)', re.DOTALL)
        scds = scd_pattern
