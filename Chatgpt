import streamlit as st
import openai
import json

# Set your OpenAI API key here
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Function to call the OpenAI API and generate IAM policy JSON based on user prompt
def generate_policy_with_llm(user_prompt, cloud_provider):
    prompt = f"Generate the JSON policy for {cloud_provider} based on the following request: {user_prompt}. Ensure the response follows the correct IAM policy structure."
    
    response = openai.Completion.create(
        model="gpt-4",  # You can also use 'text-davinci-003'
        prompt=prompt,
        temperature=0.5,
        max_tokens=500,  # Adjust this based on complexity of output
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    return response.choices[0].text.strip()

# Streamlit UI
st.title("Multi-Cloud IAM Policy Generator with LLM")

# Input: User's natural language prompt
user_input = st.text_input("Enter your permission request (e.g., 'I want only read access to S3 buckets'):")

# Dropdown for selecting cloud provider
cloud_provider = st.selectbox("Select Cloud Provider", ["AWS", "Azure", "GCP"])

# Button to generate the policy
if st.button("Generate Policy JSON"):
    if user_input:
        # Call the function to generate policy
        generated_policy = generate_policy_with_llm(user_input, cloud_provider)
        
        # Display the generated JSON policy
        st.write("Generated JSON Policy:")
        st.code(generated_policy, language="json")
    else:
        st.error("Please enter a valid permission request.")
