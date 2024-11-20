from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.config import Config
from src.model.model_trainer import ModelTrainer
import json
import random
import re
import os

class AIModel:
    def __init__(self):
        self.config = Config()  # Initialize config first
        self.model = ChatOpenAI(api_key=self.config.get_openai_api_key(), temperature=0.4)
        self.model2 = OpenAI(api_key=self.config.get_openai_api_key())
        self.model_trainer = ModelTrainer()
        
        try:
            self.vector_store = self.model_trainer.get_vector_store()
            if self.vector_store is None:
                raise ValueError("Vector store is None after initialization")
            # Verify vector store has content
            test_search = self.vector_store.similarity_search("test", k=1)
            if not test_search:
                print("Warning: Vector store appears to be empty")
        except Exception as e:
            print(f"Error Loading Vector Store: {str(e)}")
            self.vector_store = None
            
        self.scd_templates = self.load_template()
        self.scd_template_azure = self.load_azure_template()

    def load_template(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(current_dir, 'templates', 'scdTemplate.json')
            with open(template_path, 'r') as f:
                templates = json.load(f)
                return templates.get('scd_examples', [])
        except Exception as e:
            print(f"Error loading template: {e}")
            return []

    def load_azure_template(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            temp_path = os.path.join(current_dir, 'templates', 'devsecops-scd.json')
            with open(temp_path, 'r') as f:
                templates = json.load(f)
                return templates.get('Azure_SCD_template', [])
        except Exception as e:
            print(f"Error loading Azure template: {e}")
            return []

    def generate_control_id(self, resource_name):
        # Clean and validate resource name
        if not resource_name or not isinstance(resource_name, str):
            resource_name = "GenericService"
        words = resource_name.split()[:2]
        prefix = "".join([word[0].upper() for word in words if word])
        if not prefix:
            prefix = "GS"  # Generic Service fallback
        control_number = random.randint(1, 99)
        return f"{prefix}-{control_number:02d}"

    def generate_scd(self, user_prompt, service, additional_controls=None, azure_controls=None):
        if not additional_controls:
            additional_controls = []
        if not azure_controls:
            azure_controls = []

        if self.vector_store is None:
            raise ValueError("Vector store is not initialized. Please check vector store loading in ModelTrainer.")

        resource_name_match = re.search(r'\b(Azure\s\w+|AWS\s\w+|GCP\s\w+)\b', user_prompt, re.IGNORECASE)
        resource_name = resource_name_match.group(0) if resource_name_match else "GeneralService"

        # Get relevant controls from vector store
        relevant_controls = self.vector_store.similarity_search(user_prompt, k=25)
        
        # Extract control IDs and descriptions
        vector_store_controls = []
        for doc in relevant_controls:
            control_id = doc.metadata.get('control_id') if hasattr(doc, 'metadata') else self.generate_control_id(resource_name)
            vector_store_controls.append({
                'control_id': control_id,
                'description': doc.page_content
            })

        # Generate additional controls if needed
        while len(vector_store_controls) < 20:
            new_id = self.generate_control_id(resource_name)
            vector_store_controls.append({
                'control_id': new_id,
                'description': f"Additional security control for {resource_name}"
            })

        template_str = self.format_template(random.choice(self.scd_templates), resource_name)
        template_str2 = self.format_template(random.choice(self.scd_template_azure), resource_name)

        # Create prompt template
        prompt_template = PromptTemplate(
            input_variables=["control_descriptions", "user_prompt", "service", "vector_store_controls", "scd_template", "additional_controls", "azure_controls"],
            template="""
You are a cloud security expert. Based on the following control descriptions and the user's request, generate between 17 to 20 detailed SCDs.

IMPORTANT: You MUST use the following control IDs from our vector store:
{vector_store_controls}

Control descriptions from our knowledge base:
{control_descriptions}

Based on these descriptions and the following user request, generate detailed Security Control Definitions (SCDs) for the service: {service}

User request: {user_prompt}

Requirements:
1. Generate EXACTLY 17-20 SCDs (this is mandatory)
2. Use ONLY the control IDs provided above
3. Each SCD must follow this format exactly:

Control ID: [Use one of the provided control IDs]
Control Domain: [Name of the control]
Security Control For Service: [Title of the Control Domain]
Mapping to NIST CSF v1.1 control: [Relevant NIST control]
Client Requirement if any: [Put "X" for now]
Policy Name: [Policy to be used for Service Control]
Policy Description: [Brief description of the Policy Name]
Implementation Details: [Detailed steps for implementing the policy]
Responsibility: [Customer or Shared]
Frequency: [Continuous/Annual/Quarterly/Monthly]
Evidence: [Required evidence to prove control implementation]

Reference template:
{scd_template}

Additional controls to consider:
{additional_controls}

Azure-specific controls (if applicable):
{azure_controls}
"""
        )

        # Create and execute the chain
        chain = prompt_template | self.model | StrOutputParser()
        
        control_descriptions = [doc.page_content for doc in relevant_controls]
        control_ids_info = "\n".join([f"- {ctrl['control_id']}" for ctrl in vector_store_controls])
        
        response = chain.invoke({
            "control_descriptions": "\n".join(control_descriptions),
            "user_prompt": user_prompt,
            "service": service,
            "vector_store_controls": control_ids_info,
            "scd_template": template_str,
            "additional_controls": ", ".join(additional_controls),
            "azure_controls": template_str2
        })

        validated_scds = self.validate_scds(response)

        # Retry if we don't have enough SCDs
        if len(validated_scds) < 17:
            retry_prompt = f"{user_prompt}\nIMPORTANT: You MUST generate at least 17 SCDs. Current generation only produced {len(validated_scds)}."
            response = chain.invoke({
                "control_descriptions": "\n".join(control_descriptions),
                "user_prompt": retry_prompt,
                "service": service,
                "vector_store_controls": control_ids_info,
                "scd_template": template_str,
                "additional_controls": ", ".join(additional_controls),
                "azure_controls": template_str2
            })
            validated_scds = self.validate_scds(response)

        return "\n\n".join(validated_scds)

    def validate_scds(self, response):
        # Updated regex pattern to better match SCD format
        scd_pattern = re.compile(r'Control ID:.*?(?=Control ID:|$)', re.DOTALL)
        scds = scd_pattern.findall(response)
        
        validated_scds = []
        required_fields = [
            'Control ID:',
            'Control Domain:',
            'Security Control For Service:',
            'Mapping to NIST CSF v1.1 control:',
            'Client Requirement if any:',
            'Policy Name:',
            'Policy Description:',
            'Implementation Details:',
            'Responsibility:',
            'Frequency:',
            'Evidence:'
        ]
        
        for scd in scds:
            if all(field in scd for field in required_fields):
                control_id_match = re.search(r'Control ID:\s*([^\n]+)', scd)
                if control_id_match and control_id_match.group(1).strip():
                    validated_scds.append(scd.strip())
                    
        return validated_scds

    def format_template(self, template, resource_name):
        if isinstance(template, dict):
            control_id = template.get("control_id") or self.generate_control_id(resource_name)
            formatted = f"""Control ID: {control_id}
Control Domain: {template.get('control_domain', 'N/A')}
Security Control For Service: {template.get('security_control_for_service', 'N/A')}
Mapping to NIST CSF v1.1 control: {template.get('mapping_to_NIST_CSF_v1.1_control', 'N/A')}
Client Requirement if any: {template.get('client_requirement_if_any', 'N/A')}
Policy Name: {template.get('policy_name', 'N/A')}
Policy Description: {template.get('policy_description', 'N/A')}
Implementation Details:"""

            for detail in template.get("implementation_details", []):
                formatted += f"\n - {detail}"

            formatted += f"""
Responsibility: {template.get('responsibility', 'N/A')}
Frequency: {template.get('frequency', 'N/A')}
Evidence: {template.get('evidence', 'N/A')}"""

            return formatted
        return str(template)
