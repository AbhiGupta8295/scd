from dataclasses import dataclass
from typing import List, Optional, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.vectorstores.base import VectorStore
import json
import os
from pathlib import Path

@dataclass
class SecurityControl:
    control_id: str
    domain: str
    title: str
    nist_mapping: str
    client_requirement: str
    policy_name: str
    policy_description: str
    implementation_details: str
    responsibility: str
    frequency: str
    evidence: str

class SCDGenerator:
    def __init__(self, api_key: str, vector_store: VectorStore):
        self.model = ChatOpenAI(
            api_key=api_key,
            temperature=0.2  # Lower temperature for more consistent outputs
        )
        self.vector_store = vector_store
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict:
        """Load all template files from the templates directory."""
        templates = {}
        template_dir = Path(__file__).parent / 'templates'
        
        template_files = {
            'scd': 'scdTemplate.json',
            'azure': 'devsecops-scd.json',
            'edj': 'edjonesTemplate.json'
        }
        
        for key, filename in template_files.items():
            try:
                with open(template_dir / filename, 'r') as f:
                    templates[key] = json.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                templates[key] = {}
                
        return templates

    def _get_relevant_controls(self, user_prompt: str, k: int = 25) -> List[Dict]:
        """Retrieve relevant controls from vector store."""
        try:
            results = self.vector_store.similarity_search(user_prompt, k=k)
            controls = []
            
            for doc in results:
                if hasattr(doc, 'metadata') and 'control_id' in doc.metadata:
                    controls.append({
                        'control_id': doc.metadata['control_id'],
                        'content': doc.page_content,
                        'nist_mapping': doc.metadata.get('nist_mapping', 'N/A'),
                        'domain': doc.metadata.get('domain', 'General')
                    })
            
            return controls
        except Exception as e:
            print(f"Error retrieving controls: {e}")
            return []

    def generate_scd(
        self,
        service_name: str,
        user_prompt: str,
        min_controls: int = 17,
        max_controls: int = 20
    ) -> List[SecurityControl]:
        """Generate Security Control Definitions."""
        
        # Get relevant controls from vector store
        relevant_controls = self._get_relevant_controls(user_prompt)
        
        # Prepare the prompt template
        prompt_template = PromptTemplate(
            input_variables=["controls", "service", "user_prompt", "min_controls", "example_template"],
            template="""
            You are a cloud security expert generating Security Control Definitions (SCDs) for {service}.
            
            Use ONLY the following control IDs and their associated information:
            {controls}
            
            Based on this user request: {user_prompt}
            
            Generate between {min_controls} and 20 SCDs following this exact format:
            {example_template}
            
            Requirements:
            1. NEVER include the service name or cloud provider in the Control ID
            2. Use ONLY the control IDs provided above
            3. Always map to the provided NIST controls when available
            4. Keep responses consistent across multiple generations
            5. For Responsibility, use ONLY: "Customer", "Cloud Provider", or "Shared"
            6. For Frequency, use ONLY: "Continuous", "Daily", "Weekly", "Monthly", "Quarterly", or "Annually"
            
            Ensure each SCD is relevant to {service} and follows security best practices.
            """
        )
        
        # Convert controls to formatted string
        controls_str = "\n".join([
            f"Control ID: {c['control_id']}\n"
            f"Domain: {c['domain']}\n"
            f"NIST Mapping: {c['nist_mapping']}\n"
            f"Description: {c['content']}\n"
            for c in relevant_controls
        ])
        
        # Generate SCDs
        chain = prompt_template | self.model | StrOutputParser()
        response = chain.invoke({
            "controls": controls_str,
            "service": service_name,
            "user_prompt": user_prompt,
            "min_controls": min_controls,
            "example_template": json.dumps(self.templates['azure'], indent=2)
        })
        
        # Parse and validate the response
        return self._parse_scds(response)
    
    def _parse_scds(self, response: str) -> List[SecurityControl]:
        """Parse and validate generated SCDs."""
        scds = []
        current_scd = {}
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Control ID:'):
                if current_scd:
                    scds.append(SecurityControl(**current_scd))
                current_scd = {}
                current_scd['control_id'] = line.split(':', 1)[1].strip()
            elif ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                if key in SecurityControl.__annotations__:
                    current_scd[key] = value.strip()
        
        # Add the last SCD
        if current_scd:
            scds.append(SecurityControl(**current_scd))
            
        return scds

    def format_scd_output(self, scds: List[SecurityControl]) -> str:
        """Format SCDs for display or storage."""
        formatted_output = []
        
        for scd in scds:
            formatted_output.append(
                f"Control ID: {scd.control_id}\n"
                f"Control Domain: {scd.domain}\n"
                f"Control Title: {scd.title}\n"
                f"Mapping to NIST CSF v1.1 control: {scd.nist_mapping}\n"
                f"Client Requirement if Any: {scd.client_requirement}\n"
                f"Policy Name: {scd.policy_name}\n"
                f"Policy Description: {scd.policy_description}\n"
                f"Implementation Details: {scd.implementation_details}\n"
                f"Responsibility: {scd.responsibility}\n"
                f"Frequency: {scd.frequency}\n"
                f"Evidence: {scd.evidence}\n"
            )
        
        return "\n\n".join(formatted_output)
