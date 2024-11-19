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
    {scd_template}

    Azure-specific controls (if applicable):
    {azure_controls}

    Additional control areas to address:
    {additional_controls}

    Benchmark controls to consider:
    {benchmark_controls}

    FINAL CHECK:
    - Ensure you've created at least 17 SCDs
    - Verify each SCD uses a valid control ID from the provided list
    - Confirm all required sections are present in each SCD
    - Ensure SCDs are related to the cloud service mentioned in the {user_prompt}
    """
    return PromptTemplate(
        input_variables=[
            "control_descriptions",
            "user_prompt",
            "service",
            "vector_store_controls",
            "scd_template",
            "additional_controls",
            "azure_controls",
            "edj_temp",
            "benchmark_controls"
        ],
        template=template
    )

def generate_scd(self, user_prompt, service, additional_controls, azure_controls, benchmark_controls):
    # Get relevant controls from vector store
    vector_store_controls = self.get_relevant_controls(user_prompt)
    
    # Prepare control information
    control_descriptions = [ctrl['description'] for ctrl in vector_store_controls]
    control_ids_info = "\n".join([f"- {ctrl['control_id']}" for ctrl in vector_store_controls])

    # Format templates
    resource_name = self.get_resource_name(user_prompt)
    template_str = self.format_template(random.choice(self.scd_templates), resource_name)
    azure_template = self.format_template(random.choice(self.scd_template_azure), resource_name)
    edj_temp = self.format_template(random.choice(self.scd_template_edj), resource_name)

    # Create prompt template
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
        "azure_controls": azure_template,
        "edj_temp": edj_temp,
        "benchmark_controls": benchmark_controls
    })

    # Validate and potentially retry
    validated_scds = self.validate_scds(response)
    if len(validated_scds) < 17:
        retry_prompt = f"{user_prompt} IMPORTANT: You MUST generate at least 17 SCDs. Current generation only produced {len(validated_scds)}."
        response = chain.invoke({
            "control_descriptions": "\n".join(control_descriptions),
            "user_prompt": retry_prompt,
            "service": service,
            "vector_store_controls": control_ids_info,
            "scd_template": template_str,
            "additional_controls": ", ".join(additional_controls),
            "azure_controls": azure_template,
            "edj_temp": edj_temp,
            "benchmark_controls": benchmark_controls
        })
        validated_scds = self.validate_scds(response)

    return "\n\n".join(validated_scds)
