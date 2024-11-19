def generate_scd(self, user_prompt, service, additional_controls, azure_controls, benchmark_controls):
    if self.vector_store is None:
        raise ValueError("Vector store is not initialized. Please check vector store loading in ModelTrainer.")

    # Extract the service name from the prompt
    resource_name_match = re.search(r'\b(Azure\s\w+|AWS\s\w+|GCP\s\w+)\b', user_prompt, re.IGNORECASE)
    resource_name = resource_name_match.group(0) if resource_name_match else "GeneralService"

    # Fetch relevant controls from the vector store
    relevant_controls = self.vector_store.similarity_search(user_prompt, k=25)

    vector_store_controls = [
        {
            'control_id': doc.metadata.get('control_id'),
            'description': doc.page_content
        }
        for doc in relevant_controls if 'control_id' in doc.metadata
    ]

    if not vector_store_controls:
        raise ValueError("No relevant controls found in the vector store.")

    # Filter templates based on vector data control IDs
    valid_templates = [
        template for template in self.scd_templates
        if template.get("control_id") in {ctrl['control_id'] for ctrl in vector_store_controls}
    ]

    if not valid_templates:
        raise ValueError("No templates match the vector control IDs.")

    # Generate SCDs using filtered templates
    scd_list = []
    for template in valid_templates:
        formatted_template = self.format_template(template, resource_name)
        control_descriptions = "\n".join([ctrl['description'] for ctrl in vector_store_controls])
        control_ids_info = ", ".join([ctrl['control_id'] for ctrl in vector_store_controls])

        prompt_template = PromptTemplate(
            input_variables=[
                "control_descriptions", "user_prompt", "service", "control_ids", 
                "scd_template", "additional_controls", "azure_controls"
            ],
            template=(
                "You are a cloud security expert. Based on the following control descriptions and the user's request, "
                "generate detailed Security Control Definitions (SCDs) for the service: {service}. "
                "Use ONLY the control IDs provided: {control_ids}. "
                "Control descriptions: {control_descriptions}. "
                "Additional information: {additional_controls}, {azure_controls}."
            )
        )

        response = self.model.generate({
            "control_descriptions": control_descriptions,
            "user_prompt": user_prompt,
            "service": service,
            "control_ids": control_ids_info,
            "scd_template": formatted_template,
            "additional_controls": ", ".join(additional_controls),
            "azure_controls": ", ".join(azure_controls),
        })

        validated_scds = self.validate_scds(response)
        scd_list.extend(validated_scds)

        # Ensure uniqueness and limit the SCD count
        scd_list = list({scd: None for scd in scd_list}.keys())  # Deduplicate
        if len(scd_list) >= 17:
            break

    if len(scd_list) < 17:
        raise ValueError("Failed to generate at least 17 unique SCDs.")

    return "\n\n".join(scd_list)
