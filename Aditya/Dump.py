[11/19, 11:29 PM] Aditya: You, 13 minutes ago | 2 authors (You and one other)

1

import json

2

import random

3

import re

4

import os

5

from openai import OpenAI

6

from src.utils.config import Config

7

from langchain_openai import ChatOpenAI

8

from src.data.io_handler import IOHandler

9

from langchain.prompts import PromptTemplate

0 from src.model.model Trainer import ModelTrainer

1

from langchain_core.output_parsers import StrOutputParser

2

3

4

5

6

7

8

9

20

21

2

23

24

25

26

27

You, 13 minutes ago | 2 authors (You and one other)

class AIModel:

def _init_(self):

self.config= Config()

self.model = ChatOpenAI(api_key=self.config.get_openai_spi_key(), temperature 0.2)

self.model2 = OpenAI(api_key=self.config.get_openai_api_key())

self.model_trainer ModelTrainer()

self.io_handler 10Handler()

try:

self.vector_store = self.model_trainer.get_vector_store()

except Exception as e:

print(f"Error Loading Vector Store: (str(e)}")

self.vector_store = None

self.scd_templates = self.load_template()

self.scd_template_azure = self.load_azure_template()

self.scd_template_edj = self.load_azure_edj_template()

def load_template(self):

try:

current_dir = os.path.dirname(os.path.abspath(_file_))

template_path = os.path.join(current_dir, 'templates', 'scdTemplate.json') with open(template_path, 'r') as f:

return json.load(f).get('data', [])

except Exception as e:

print(f"Error loading template: {e}")

return []

42

def load_azure_template(self):

43

44

45

46

47

48

49

try:

current_dir2 = os.path.dirname(os.path.abspath(_file_))

temp_path = os.path.join(current_dir2, 'templates', 'devsecops-scd.json') with open(temp_path, 'r') as f:

return json.load(f).get('Azure_SCD_template', [])

except Exception as e:

print(f"Error loading Azure SCD template: {e}")

50

return []

51

52

def load_azure_edj_template(self):

53

try:

54

current dir3= os.path.dirname(os.path.abspath(_file_)

temp_path = os.path.join(current_dir3, 'templates', 'edjones Template.json')

with open(temp_path, 'r') as f:

return json.load(f).get('edj_scd_template', [])

except Exception as e:

print(f"Error loading EDJ SCD template: {e}")

return []

def generate_scd(self, user_prompt, service, additional_controls, azure_controls, benchmark_controls):

if self.vector_store is None:

raise ValueError("Vector store is not initialized. Please check vector store loading in ModelTrainer.")

resource_name_match = re.search(r'\b(Azure\s\w+|AWS\s\w+|GCP\s\w+)\b', user_prompt, re. IGNORECASE) resource_name = resource_name_match.group(8) if resource_name_match else "GeneralService"

relevant_controls = self.vector_store.similarity_search(user_prompt, k=25 You, last week update: updated scd format, co

relavant_control_ids = self.vector_store.similarity_search(user_prompt, k=25)

# Extract control IDs and descriptions from vector store results

vector_store_controls = []

for doc in relevant_controls:

#Assuming the vector store documents have metadata with control_id

control_id=doc.metadata.get('control_id') if hasattr(doc, 'metadata') else None

if control_id:

vector_store_controls.append({

'control_id': control_id,

'description': doc.page_content

})
[11/19, 11:30 PM] Aditya: template_str = self.format_template(random.choice(self.scd_templates), resource_name)

template_str2 = self.format_template(random.choice(self.scd_template_azure), resource_name)

edj_temp = self.format_template(random.choice(self.scd_template_edj ), resource_name)

prompt_template PromptTemplate(

input_variables=["control_descriptions", "user_prompt", "service", "control_ids", "scd_template", "additional_controls", "azure template=""

You are a cloud security expert. Based on the following control descriptions and the user's request, generate between 17 to 20 detailed Sec

IMPORTANT: You MUST use the following control IDs from our vector store. These are the only valid control IDs you should use:

{{vector_store_controls}}

IMPORTANT RULES:

I

96

2. Use ONLY the control IDs from the provided vector store controls

07

3. Always map controls to NIST CSF v1.1 when available in the vector store data

28

4. For Responsibility, use ONLY: "Customer", "Cloud Provider", or "Shared"

29

5. For Frequency, use ONLY: "Continuous", "Daily", "Weekly", "Monthly", "Quarterly", or "Annually"

10

11

Control descriptions from our knowledge base:

12

(control_descriptions)

13

14

Based on these descriptions and the following user request, generate detailed Security Control Definitions (SCDs) for the service: (service

15

16

User request: (user_prompt}

17

Service: (service)

Requirements:

1. Generate EXACTLY 17-20 SCDs this is mandatory

2. Use ONLY the control IDs provided above from the vector dataset

3. Each SCD must follow this format:

Control ID: Check upon the vector images of the dataset ({vector_store_controls)), analyse the control Domain & map the control id for the Control Domain: [Name of the control] [The Basis Benchmark we group controls within the following domains] [Check upon the vector images of

Control Title: [This is the Azure Security Benchmark Control Title.]

Mapping to NIST CSF v1.1 control: Check upon the vector images of the dataset ((vector_store_controls)), analyse the nist cloud security be

Client Requirement if Any: Leave it blank or just put a "X"

Policy Name: [Mapped to the azure security benchmark "Feature Name"]

Policy Description: [Brief description of the Policy Name] [Mapped to the azure security benchmark "Feature Description"]

Implementation Details: [This will be mapped to Guidance] [Detailed steps for implementing the control, Best Practices to maintain cloud se

Responsibility: [Customer/Cloud Provider/Shared] [Map it according to the azure security benchmark "Responsibility"]

Frequency: [How often should this control be reviewed/implemented & monitored/checked upon? Choose between Continuous / Annual Review / Qua Evidence: [What evidence is required to prove this control is in place? What are we referring to?] [Required evidence for compliance]

Here's an example template for a well-formatted SCD, Refer to this JSON template which includes well best practices following SCDs for diff

{{edj_temp}}

Here's a well-curated & manually formatted Security Control Definitions for Microsoft Azure, Refer to this JSON template to create the SCDs

((template_str2}}

When the (user_prompt) is based on azure cloud services, check if these controls are relevant to the service mentioned or not, if it's ther

((benchmark_controls}}
[11/19, 11:33 PM] Aditya: For each SCD, provide your response in the same format as the template above. Ensure each SCD is unique and relevant to the user's request.

In addition to the general security controls, make sure to include SCDs that specifically address the following control areas:

(azure_controls)

FINAL CHECK:

Ensure you've created at least 17 SCDS

Verify each SCD uses a valid control ID from the provided list

Confirm all required sections are present in each SCD

)

#Prepare control information for the prompt

control_descriptions [doc.page_content for doc in relevant_controls] control_ids_info = "\n".join([f"- (ctrl['control_id']}" for ctrl in vector_store_controls])

chain prompt_template | self.model | StrOutputParser()

response chain.invoke({

"control_descriptions": "\n".join(control_descriptions),

"user_prompt": user_prompt,

"service": service,

"vector_store_controls": control_ids_info,

"scd_template": template_str, "additional_controls": ", ".join(additional_controls),

"azure_controls": template_str2

validated_scds = self.validate_scds(response)

#If we don't get enough SCDs, try one more time with a stronger emphasis

if len(validated_scds) < 17:

retry_prompt = f"(user_prompt) IMPORTANT: You MUST generate at least 17 SCDs. Current generation only produced (len(validated_scds))

response chain.invoke({

"control_descriptions": "\n".join(control_descriptions),

"user_prompt": retry_prompt,

"service": service,

"vector_store_controls": control_ids_info,

"scd_template": template_str,

"additional_controls": ", ".join(additional_controls),

"azure_controls": template_str2

I

validated_scds self.validate_scds(response)

return "\n\n".join(validated_scds)

ef validate_scds(self, response):

scd_pattern = re.compile(r'Control ID:.*?(?=Control ID: 1$)', re.DOTALL)

scds = scd_pattern.findall(response)

validated_scds = []

for scd in scds:

Enhanced validation

required_fields = ['Control ID:', 'Control Domain:', 'Control Title:',

'Mapping to NIST CSF v1.1 control:', 'Client Requirement if Any:',

'Policy Name:', 'Policy Description:', 'Implementation Details:',

'Responsibility:', 'Frequency:', 'Evidence:']

if all(field in scd for field in required_fields):

#Extract control ID for additional validation

control_id_match = re.search(r'Control ID:\s*([^\n]+)', scd) if control_id_match and control_id_match.group(1).strip():

validated_scds.append(scd.strip())

return validated_scds

def format_template(self, template, resource_name):

if isinstance(template, dict):

#control_id = template.get("control_id") or self.generate_control_id(resource_name)

control_id = template.get(" mplate.get("control_id")

I

formatted = "Control ID: {control_id}\n"

formatted += f"Control Domain: (template.get('control_domain', 'N/A')}\n"

formatted += f"Control Title: (template.get('control_title', 'N/A')}\n"

91

2

3

4

5

6

7

8

9

1

2

5

formatted += f"Mapping to NIST CSF v1.1 control: (template.get('mapping_to_NIST_CSF_v1.1_control', 'N/A')}\n"

formatted += f"Client Requirement if Any: (template.get('client_requirement_if_any', 'N/A')}\n"

formatted += f"Policy Name: (template.get('policy_name', 'N/A')}\n"

formatted += f"Policy Description [template.get('policy_description', 'N/A')}\n"

formatted += "Implementation Details: \n"

for detail in template.get("implementation_details", []):

formatted += +" || (detail)\n"

formatted += f"Responsibility: [template.get('responsibility'. 'N/A')\n

formatted += f"Evidence: (template.get('evidence', 'N/A')}"

230

Ο 231

return formatted

return ""

0

2

I
