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
        """Initialize the vector store with security controls."""
        try:
            # Load the vector store directly from the model trainer
            self.vector_store = self.model_trainer.get_vector_store()
            if not isinstance(self.vector_store, FAISS):
                raise ValueError("Expected FAISS vector store")
            
            # Verify vector store has content
            test_search = self.vector_store.similarity_search("security", k=1)
            if not test_search:
                raise ValueError("Vector store appears to be empty")
                
        except Exception as e:
            print(f"Vector store initialization failed: {str(e)}")
            raise

    def initialize_templates(self) -> None:
        """Initialize all required templates."""
        self.scd_templates = self.load_template()
        self.scd_template_azure = self.load_azure_template()
        self.scd_template_edj = self.load_azure_edj_template()

    def load_template(self) -> List[Dict[str, Any]]:
        """Load the main SCD template."""
        return self._load_json_template('scdTemplate.json', 'data')

    def load_azure_template(self) -> List[Dict[str, Any]]:
        """Load the Azure-specific template."""
        return self._load_json_template('devsecops-scd.json', 'Azure_SCD_template')

    def load_azure_edj_template(self) -> List[Dict[str, Any]]:
        """Load the EDJ template."""
        return self._load_json_template('edjonesTemplate.json', 'edj_scd_template')

    def _load_json_template(self, filename: str, key: str) -> List[Dict[str, Any]]:
        """Load and parse a JSON template file."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(current_dir, 'templates', filename)
            with open(template_path, 'r') as f:
                return json.load(f).get(key, [])
        except Exception as e:
            print(f"Error loading template {filename}: {str(e)}")
            return []

    def get_resource_name(self, user_prompt: str) -> str:
        """Extract the resource name from the user prompt."""
        resource_match = re.search(
            r'\b(Azure\s\w+|AWS\s\w+|GCP\s\w+)\b',
            user_prompt,
            re.IGNORECASE
        )
        return resource_match.group(0) if resource_match else "GeneralService"

    def get_relevant_controls(self, user_prompt: str, k: int = 25) -> List[Dict[str, str]]:
        """Get relevant security controls based on the user prompt."""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")

        # Prepare search terms
        search_terms = [
            user_prompt,  # Original prompt
            f"security controls {user_prompt}",  # Security-focused
            f"compliance requirements {user_prompt}"  # Compliance-focused
        ]
        
        all_controls = []
        seen_control_ids = set()
        
        # Try each search term
        for search_term in search_terms:
            try:
                results = self.vector_store.similarity_search(search_term, k=k)
                
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
                        
            except Exception as e:
                print(f"Search failed for term '{search_term}': {str(e)}")
                continue
        
        # If we still don't have enough controls, try a more generic search
        if len(all_controls) < 10:
            try:
                generic_results = self.vector_store.similarity_search("security compliance controls", k=k)
                for doc in generic_results:
                    if not hasattr(doc, 'metadata') or 'control_id' not in doc.metadata:
                        continue
                        
                    control_id = doc.metadata['control_id']
                    if control_id not in seen_control_ids:
                        seen_control_ids.add(control_id)
                        all_controls.append({
                            'control_id': control_id,
                            'description': doc.page_content
                        })
            except Exception as e:
                print(f"Generic search failed: {str(e)}")

        return all_controls[:k]  # Return at most k controls

    def generate_scd(self, user_prompt: str, service: str, additional_controls: List[str], 
                    azure_controls: str, benchmark_controls: str) -> str:
        """Generate Security Control Definitions based on user requirements."""
        try:
            # Get relevant controls
            vector_store_controls = self.get_relevant_controls(user_prompt)
            if not vector_store_controls:
                raise ValueError("No relevant controls found in vector store")

            # Prepare control information
            control_descriptions = [ctrl['description'] for ctrl in vector_store_controls]
            control_ids_info = "\n".join([f"- {ctrl['control_id']}" for ctrl in vector_store_controls])

            # Format templates
            resource_name = self.get_resource_name(user_prompt)
            template_str = self.format_template(random.choice(self.scd_templates), resource_name)
            template_str2 = self.format_template(random.choice(self.scd_template_azure), resource_name)
            edj_temp = self.format_template(random.choice(self.scd_template_edj), resource_name)

            # Create and run the generation chain
            prompt_template = self.create_scd_prompt_template()
            chain = prompt_template | self.model | StrOutputParser()

            # Generate initial response
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

            # Validate and potentially retry
            validated_scds = self.validate_scds(response)
            if len(validated_scds) < 17:
                retry_prompt = (f"{user_prompt} IMPORTANT: You MUST generate at least 17 SCDs. "
                              f"Current generation only produced {len(validated_scds)}.")
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
            error_msg = f"Failed to generate SCDs: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

    def create_scd_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for SCD generation."""
        template = """
        You are a cloud security expert. Based on the following control descriptions and the user's request, generate between 17 to 20 detailed Security Control Definitions (SCDs).

        IMPORTANT: You MUST use the following control IDs from our vector store. These are the only valid control IDs you should use:
        {vector_store_controls}

        IMPORTANT RULES:
        1. DO NOT include service names or cloud provider names in Control IDs
        2. Use ONLY the control IDs from the provided vector store controls
        3. Always map controls to NIST CSF v1.1 when available in the vector store data
        4. Each SCD must be comprehensive and implementable

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

    def validate_scds(self, response: str) -> List[str]:
        """Validate the generated SCDs and ensure they meet all requirements."""
        scd_pattern = re.compile(r'Control ID:.*?(?=Control ID:|$)', re.DOTALL)
        scds = scd_pattern.findall(response)
        
        required_fields = [
            'Control ID:', 'Control Domain:', 'Control Title:',
            'Mapping to NIST CSF v1.1 control:', 'Client Requirement if Any:',
            'Policy Name:', 'Policy Description:', 'Implementation Details:',
            'Responsibility:', 'Frequency:', 'Evidence:'
        ]
        
        validated_scds = []
        for scd in scds:
            if all(field in scd for field in required_fields):
                control_id_match = re.search(r'Control ID:\s*([^\n]+)', scd)
                if control_id_match and control_id_match.group(1).strip():
                    validated_scds.append(scd.strip())
        
        return validated_scds

    def format_template(self, template: Dict[str, Any], resource_name: str) -> str:
        """Format the template with the given resource name."""
        if not isinstance(template, dict):
            return ""
            
        formatted = []
        fields = [
            ('control_id', 'Control ID'),
            ('control_domain', 'Control Domain'),
            ('control_title', 'Control Title'),
            ('mapping_to_NIST_CSF_v1.1_control', 'Mapping to NIST CSF v1.1 control'),
            ('client_requirement_if_any', 'Client Requirement if Any'),
            ('policy_name', 'Policy Name'),
            ('policy_description', 'Policy Description')
        ]
        
        for key, label in fields:
            value = template.get(key, 'N/A')
            if isinstance(value, str):
                value = value.replace('{resource_name}', resource_name)
            formatted.append(f"{label}: {value}")
        
        # Handle implementation details
        formatted.append("Implementation Details:")
        for detail in template.get("implementation_details", []):
            if isinstance(detail, str):
                detail = detail.replace('{resource_name}', resource_name)
            formatted.append(f" || {detail}")
        
        # Add remaining fields
        remaining_fields = [
            ('responsibility', 'Responsibility'),
            ('frequency', 'Frequency'),
            ('evidence', 'Evidence')
        ]
        
        for key, label in remaining_fields:
            value = template.get(key, 'N/A')
            if isinstance(value, str):
                value = value.replace('{resource_name}', resource_name)
            formatted.append(f"{label}: {value}")
        
        return "\n".join(formatted)
