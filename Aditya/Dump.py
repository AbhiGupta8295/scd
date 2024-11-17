from langchain_openai import OpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.config import Config
from src.model.model_trainer import ModelTrainer
from src.data.io_handler import IOHandler
import json
import os

class AIModel:
    def __init__(self):
        self.config = Config()
        # Reduced temperature for more consistent outputs
        self.model = ChatOpenAI(
            api_key=self.config.get_openai_api_key(), 
            temperature=0.2
        )
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

        # Get relevant controls from vector store
        relevant_controls = self.vector_store.similarity_search(user_prompt, k=25)

        # Extract control IDs and descriptions from vector store results
        vector_store_controls = []
        for doc in relevant_controls:
            if hasattr(doc, 'metadata') and 'control_id' in doc.metadata:
                vector_store_controls.append({
                    'control_id': doc.metadata['control_id'],
                    'description': doc.page_content,
                    'nist_mapping': doc.metadata.get('nist_mapping', 'N/A'),
                    'domain': doc.metadata.get('domain', 'General')
                })

        template_str = self.format_template(random.choice(self.scd_templates))
        template_str2 = self.format_template(random.choice(self.scd_template_azure))
        edj_temp = self.format_template(random.choice(self.scd_template_edj))

        # Updated prompt template to fix the issues
        prompt_template = PromptTemplate(
            input_variables=["control_descriptions", "user_prompt", "service", "control_ids", "scd_template", "additional_controls", "azure_controls", "benchmark_controls"],
            template="""
            You are a cloud security expert. Generate between 17-20 Security Control Definitions (SCDs) based on the following information.

            IMPORTANT RULES:
            1. DO NOT include service names or cloud provider names in Control IDs
            2. Use ONLY the control IDs from the provided vector store controls
            3. Always map controls to NIST CSF v1.1 when available in the vector store data
            4. For Responsibility, use ONLY: "Customer", "Cloud Provider", or "Shared"
            5. For Frequency, use ONLY: "Continuous", "Daily", "Weekly", "Monthly", "Quarterly", or "Annually"

            Vector Store Controls:
            {control_ids}

            Control descriptions from our knowledge base:
            {control_descriptions}

            User request: {user_prompt}
            Service: {service}

            Each SCD must follow this exact format:
            Control ID: [MUST use only IDs from vector store]
            Control Domain: [Domain from vector store or appropriate security domain]
            Control Title: [Clear, concise title]
            Mapping to NIST CSF v1.1 control: [Use mapping from vector store if available]
            Client Requirement if Any: [If none, put "N/A"]
            Policy Name: [Relevant policy name]
            Policy Description: [Clear description of the policy]
            Implementation Details: [Specific, actionable steps]
            Responsibility: [Customer/Cloud Provider/Shared]
            Frequency: [Continuous/Daily/Weekly/Monthly/Quarterly/Annually]
            Evidence: [Required evidence for compliance]

            Reference Templates:
            {scd_template}
            
            Azure-specific template:
            {azure_controls}

            Additional controls to consider:
            {additional_controls}

            Benchmark controls:
            {benchmark_controls}
            """
        )

        # Generate SCDs
        control_descriptions = [doc.page_content for doc in relevant_controls]
        control_ids_info = "\n".join([f"- {ctrl['control_id']} (NIST: {ctrl['nist_mapping']})" 
                                    for ctrl in vector_store_controls])

        chain = prompt_template | self.model | StrOutputParser()
        response = chain.invoke({
            "control_descriptions": "\n".join(control_descriptions),
            "user_prompt": user_prompt,
            "service": service,
            "control_ids": control_ids_info,
            "scd_template": template_str,
            "additional_controls": ", ".join(additional_controls),
            "azure_controls": template_str2,
            "benchmark_controls": benchmark_controls
        })

        validated_scds = self.validate_scds(response)

        # If we don't get enough SCDs, try one more time
        if len(validated_scds) < 17:
            retry_prompt = f"{user_prompt} IMPORTANT: You MUST generate at least 17 SCDs."
            response = chain.invoke({
                "control_descriptions": "\n".join(control_descriptions),
                "user_prompt": retry_prompt,
                "service": service,
                "control_ids": control_ids_info,
                "scd_template": template_str,
                "additional_controls": ", ".join(additional_controls),
                "azure_controls": template_str2,
                "benchmark_controls": benchmark_controls
            })
            validated_scds = self.validate_scds(response)

        return "\n\n".join(validated_scds)

    def validate_scds(self, response):
        """Validate and clean up generated SCDs."""
        scd_pattern = re.compile(r'Control ID:.*?(?=Control ID:|$)', re.DOTALL)
        scds = scd_pattern.findall(response)
        validated_scds = []

        required_fields = [
            'Control ID:', 'Control Domain:', 'Control Title:', 
            'Mapping to NIST CSF v1.1 control:', 'Client Requirement if Any:', 
            'Policy Name:', 'Policy Description:', 'Implementation Details:', 
            'Responsibility:', 'Frequency:', 'Evidence:'
        ]

        for scd in scds:
            # Check if all required fields are present
            if all(field in scd for field in required_fields):
                # Validate Control ID format (ensure no service/cloud provider names)
                control_id_match = re.search(r'Control ID:\s*([^\n]+)', scd)
                if control_id_match:
                    control_id = control_id_match.group(1).strip()
                    # Ensure control ID doesn't contain service names
                    if not any(name.lower() in control_id.lower() 
                             for name in ['azure', 'aws', 'gcp', 'cloud']):
                        validated_scds.append(scd.strip())

        return validated_scds
