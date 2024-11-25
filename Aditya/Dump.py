class AIModel:
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
                formatted += f"\n- {detail}"

            formatted += f"""
Responsibility: {template.get('responsibility', 'N/A')}
Frequency: {template.get('frequency', 'N/A')}
Evidence: {template.get('evidence', 'N/A')}"""

            return formatted
        return str(template)

    def validate_scds(self, response):
        # Updated regex pattern to better match SCD format without stars
        scd_pattern = re.compile(r'Control ID:\s*(?:.*?)(?=Control ID:|$)', re.DOTALL)
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
                    # Clean up any extra whitespace and remove any asterisks
                    cleaned_scd = scd.strip()
                    # Remove any asterisks and clean up extra whitespace
                    cleaned_scd = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_scd)
                    # Remove extra newlines
                    cleaned_scd = re.sub(r'\n\s*\n', '\n', cleaned_scd)
                    validated_scds.append(cleaned_scd)

        return validated_scds

    def generate_scd(self, user_prompt, service, additional_controls=None, azure_controls=None):
        # ... rest of the generate_scd method remains the same ...
        # Update the prompt template to not include asterisks
        prompt_template = PromptTemplate(
            input_variables=["control_descriptions", "user_prompt", "service", "vector_store_controls", "scd_template", "additional_controls", "azure_template"],
            template="""You are a cloud security expert. Based on the following control descriptions and the user's request, generate SCDs without any asterisks or markdown formatting. Format each SCD exactly as follows:

Control ID: [ID]
Control Domain: [Domain]
Security Control For Service: [Title]
...
[rest of your existing template without asterisks]
""")
        
        # ... rest of the method implementation ...
