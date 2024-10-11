#--------------------------remove extra unwanted permission from users----------------------
import boto3
from datetime import datetime, timedelta
import csv

# Create a session using boto3
iam_client = boto3.client('iam')
cloudtrail_client = boto3.client('cloudtrail')

# Define the time period for 3 months
time_threshold = datetime.utcnow() - timedelta(days=90)

# Get all IAM users
def list_users():
    users = []
    try:
        paginator = iam_client.get_paginator('list_users')
        for response in paginator.paginate():
            users.extend(response['Users'])
    except Exception as e:
        print(f"Error retrieving users: {str(e)}")
    return users

# List all roles assigned to a specific user (from policies or role assumptions)
def get_user_roles(user_name):
    roles = []
    try:
        # List attached user policies and look for roles within them
        response = iam_client.list_attached_user_policies(UserName=user_name)
        for policy in response['AttachedPolicies']:
            # Get policy document and check for role usage
            policy_arn = policy['PolicyArn']
            policy_doc = iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=iam_client.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
            )
            # Check if the policy document allows any roles (this is a simplified check)
            if 'AssumeRole' in str(policy_doc):
                roles.append(policy_arn)  # Add the role if found
    except Exception as e:
        print(f"Error retrieving roles for user {user_name}: {str(e)}")
    return roles

# Get CloudTrail events for role usage
def get_role_usage(role_name):
    last_used = None
    frequency = 0
    try:
        # Search CloudTrail events for role assumption
        response = cloudtrail_client.lookup_events(
            LookupAttributes=[{'AttributeKey': 'EventName', 'AttributeValue': 'AssumeRole'}],
            StartTime=time_threshold,  # Limit to past 3 months
            EndTime=datetime.utcnow()
        )
        for event in response['Events']:
            if role_name in event['Resources']:
                event_time = event['EventTime']
                frequency += 1
                if not last_used or event_time > last_used:
                    last_used = event_time
    except Exception as e:
        print(f"Error retrieving CloudTrail events for role {role_name}: {str(e)}")
    return last_used, frequency

# Generate a report with user-role mapping, last usage, and frequency
def generate_user_role_report():
    report = []
    users = list_users()
    for user in users:
        user_name = user['UserName']
        user_roles = get_user_roles(user_name)
        for role in user_roles:
            last_used, frequency = get_role_usage(role)
            report.append({
                'UserName': user_name,
                'RoleName': role,
                'LastUsed': last_used or 'Never',
                'UsageFrequency': frequency
            })
    return report

# Save the report to a CSV file
def save_report_to_csv(report, filename="user_role_report.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['UserName', 'RoleName', 'LastUsed', 'UsageFrequency'])
        writer.writeheader()
        for row in report:
            writer.writerow(row)
    print(f"Report saved to {filename}")

if __name__ == "__main__":
    # Step 1: Generate the user-role report
    report = generate_user_role_report()
    
    # Step 2: Save the report to a CSV file
    save_report_to_csv(report)

#-----------------------------------------------------------------------------------------------------------------

#------------------------------------io_handler.py------------------------------------
import csv
import os

class IOHandler:
    def __init__(self, input_dir='input', output_dir='output'):
        self.input_dir = input_dir
        self.output_dir = output_dir

        # Create directories if they do not exist
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def read_csv(self, filename):
        """Read input data from a CSV file."""
        file_path = os.path.join(self.input_dir, filename)
        data = []
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    data.append(row)
            return data
        except FileNotFoundError:
            print(f"File {file_path} not found. Please ensure the file is in the correct directory.")
            return None
        except Exception as e:
            print(f"Error reading file {filename}: {str(e)}")
            return None

    def write_output(self, filename, content):
        """Write the generated SCD output to a text file."""
        file_path = os.path.join(self.output_dir, filename)
        try:
            with open(file_path, mode='w', encoding='utf-8') as file:
                file.write(content)
            print(f"Output successfully written to {file_path}")
        except Exception as e:
            print(f"Error writing to file {filename}: {str(e)}")

    def get_user_input(self, prompt_text):
        """Interact with user to get dynamic input."""
        return input(prompt_text)

    def list_input_files(self):
        """List available CSV files in the input directory."""
        files = [f for f in os.listdir(self.input_dir) if f.endswith('.csv')]
        if not files:
            print(f"No CSV files found in {self.input_dir}")
        return files

    def display_data(self, data):
        """Pretty print the loaded data."""
        for index, row in enumerate(data, start=1):
            print(f"Record {index}: {row}")

 #--------------------------------------------------__-------------------------------------------------


#----------------------------------ai playground request------------------------------------------------
import requests
import json

# Replace with your deployed AI model URL
AI_MODEL_URL = "https://your-deployed-ai-model-url.com/api"

# Define the payload data
payload = {
    "system_prompt": "Your system prompt here",
    "user_prompt": "Your user prompt here",
    "user_query": "Your user query here",
    "parsed_content": "Your parsed content here",
    "document": None  # Placeholder for your document dataset
}

# Specify headers for the request
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY_HERE",  # Replace with your API key or token if required
}

# Function to send POST request with JSON payload and document
def send_request_with_document(document_path=None):
    if document_path:
        # If a document is provided, read it and include it in the payload
        with open(document_path, 'r') as file:
            document_data = file.read()
        payload["document"] = document_data

    # Send the POST request
    response = requests.post(AI_MODEL_URL, headers=headers, data=json.dumps(payload))

    # Check the response
    if response.status_code == 200:
        print("Request successful!")
        print("Response:", response.json())
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response:", response.text)

# Example usage
document_path = "path/to/your/document.txt"  # Replace with the actual document file path
send_request_with_document(document_path)

#-------------------------------------------------------------------------------------------------------------
pip install google-api-python-client google-auth google-cloud-logging google-cloud-resourcemanager

import os
import datetime
from google.auth import default
from googleapiclient.discovery import build
from google.cloud import logging_v2

# Define time threshold (3 months ago)
time_threshold = datetime.datetime.utcnow() - datetime.timedelta(days=90)

# Authentication using default credentials (e.g., service account)
credentials, project_id = default()

# Initialize the IAM and Logging services
iam_service = build('iam', 'v1', credentials=credentials)
logging_client = logging_v2.Client()

# List all users and their assigned roles (bindings)
def list_iam_roles():
    roles_to_check = []
    request = iam_service.projects().getIamPolicy(resource=project_id, body={})
    policy = request.execute()
    
    for binding in policy['bindings']:
        role = binding['role']
        members = binding.get('members', [])
        for member in members:
            if member.startswith('user:'):  # Only checking user accounts
                roles_to_check.append({'user': member, 'role': role})
    
    return roles_to_check

# Query Cloud Logging for the role usage (fetch IAM policy changes)
def check_role_usage(user_email, role):
    #filter_str = f"""
   # protoPayload.authenticationInfo.principalEmail="{user_email}" AND\
  #  protoPayload.serviceName="iam.googleapis.com" AND\
  #  protoPayload.methodName="SetIamPolicy" AND\
 #   protoPayload.authorizationInfo.resource="projects/{project_id}" AND\
 #   resource.labels.role="{role}"\"""
    
    usage_found = False
    last_used = None

    for entry in logging_client.list_entries(filter_=filter_str):
        log_time = entry.timestamp
        
        if log_time and log_time > time_threshold:
            last_used = log_time
            usage_found = True
            break

    return last_used if usage_found else None

# Revoke unused roles by updating IAM policy
def revoke_unused_roles(unused_roles):
    policy = iam_service.projects().getIamPolicy(resource=project_id, body={}).execute()
    bindings = policy['bindings']

    # Filter out unused roles from the policy
    for unused_role in unused_roles:
        for binding in bindings:
            if binding['role'] == unused_role['role'] and unused_role['user'] in binding['members']:
                binding['members'].remove(unused_role['user'])
                print(f"Revoked {unused_role['role']} from {unused_role['user']}")
                break

    # Update the IAM policy
    body = {'policy': policy}
    iam_service.projects().setIamPolicy(resource=project_id, body=body).execute()

# Main function
def main():
    roles = list_iam_roles()
    unused_roles = []

    # Check last usage of each role
    for role in roles:
        user = role['user']
        assigned_role = role['role']
        last_used = check_role_usage(user, assigned_role)
        
        if last_used is None:
            print(f"Role {assigned_role} assigned to {user} has not been used in the last 3 months.")
            unused_roles.append(role)
        else:
            print(f"Role {assigned_role} assigned to {user} was last used on {last_used}.")

    # Revoke unused roles
    if unused_roles:
        revoke_unused_roles(unused_roles)
    else:
        print("No unused roles found.")

if __name__ == "__main__":
    main()
  
#---------------------------------_-----------------------------------------
#https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-google-cloud-platform
import datetime
import csv
from google.auth import default
from googleapiclient.discovery import build
from google.cloud import logging_v2

# Define time threshold (3 months ago) and make it timezone-aware
time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)

# Authentication using default credentials (e.g., service account)
credentials, project_id = default()

# Initialize the Resource Manager and Logging services
crm_service = build('cloudresourcemanager', 'v1', credentials=credentials)
logging_client = logging_v2.Client()

# List all users and their assigned roles (IAM bindings)
def list_iam_roles():
    roles_to_check = []
    
    # Get the IAM policy for the project
    policy_request = crm_service.projects().getIamPolicy(resource=project_id, body={})
    policy = policy_request.execute()
    
    for binding in policy['bindings']:
        role = binding['role']
        members = binding.get('members', [])
        for member in members:
            if member.startswith('user:'):  # Only checking user accounts
                roles_to_check.append({'user': member, 'role': role})
    
    return roles_to_check

# Query Cloud Logging for the role usage (fetch IAM policy changes)
def check_role_usage(user_email, role):
 
    
    usage_found = False
    last_used = None

    for entry in logging_client.list_entries(filter_=filter_str):
        log_time = entry.timestamp
        
        # Ensure log_time is timezone-aware
        if log_time.tzinfo is None:
            log_time = log_time.replace(tzinfo=datetime.timezone.utc)

        if log_time and log_time > time_threshold:
            last_used = log_time
            usage_found = True
            break

    return last_used if usage_found else None

# Write the results to a CSV file
def write_to_csv(data, filename='role_usage_report.csv'):
    with open(filename, mode='w', newline='') as csvfile:
        fieldnames = ['User', 'Role', 'Last Used', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the data rows
        for row in data:
            writer.writerow(row)

    print(f"Report written to {filename}")

# Revoke unused roles by updating IAM policy
def revoke_unused_roles(unused_roles):
    # Get the current IAM policy for the project
    policy_request = crm_service.projects().getIamPolicy(resource=project_id, body={})
    policy = policy_request.execute()
    
    bindings = policy['bindings']

    # Filter out unused roles from the policy
    for unused_role in unused_roles:
        for binding in bindings:
            if binding['role'] == unused_role['role'] and unused_role['user'] in binding['members']:
                binding['members'].remove(unused_role['user'])
                print(f"Revoked {unused_role['role']} from {unused_role['user']}")
                break

    # Update the IAM policy to remove unused roles
    body = {'policy': policy}
    crm_service.projects().setIamPolicy(resource=project_id, body=body).execute()

# Main function
def main():
    roles = list_iam_roles()
    unused_roles = []
    csv_data = []

    # Check last usage of each role
    for role in roles:
        user = role['user']
        assigned_role = role['role']
        last_used = check_role_usage(user, assigned_role)

        if last_used is None:
            print(f"Role {assigned_role} assigned to {user} has not been used in the last 3 months.")
            unused_roles.append(role)
            csv_data.append({
                'User': user,
                'Role': assigned_role,
                'Last Used': 'Never Used',
                'Status': 'To be revoked'
            })
        else:
            print(f"Role {assigned_role} assigned to {user} was last used on {last_used}.")
            csv_data.append({
                'User': user,
                'Role': assigned_role,
                'Last Used': last_used.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Active'
            })

    # Write to CSV
    write_to_csv(csv_data)

    # Revoke unused roles
    if unused_roles:
        revoke_unused_roles(unused_roles)
    else:
        print("No unused roles found.")

if __name__ == "__main__":
    main()
    
#--------------------------------------------------------------------------------
import os
import google.auth
from google.auth.transport.requests import Request
from google.auth import impersonated_credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from requests.exceptions import HTTPError
import time

# Retry logic for token refresh
def refresh_credentials_with_retry(credentials, max_retries=3, delay=2):
    for i in range(max_retries):
        try:
            credentials.refresh(Request())
            return credentials
        except HTTPError as e:
            if i < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise e

# Set up impersonated credentials
def get_impersonated_credentials():
    service_account_credentials = service_account.Credentials.from_service_account_file(
        'your-service-account.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    target_principal = os.environ.get('TARGET_SERVICE_ACCOUNT')  # Target service account to impersonate
    
    # Create impersonated credentials
    credentials = impersonated_credentials.Credentials(
        source_credentials=service_account_credentials,
        target_principal=target_principal,
        target_scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    # Refresh the impersonated credentials with retry logic
    return refresh_credentials_with_retry(credentials)

# Use impersonated credentials to make API calls
def list_iam_roles():
    try:
        # Get impersonated credentials
        credentials = get_impersonated_credentials()
        
        # Initialize Resource Manager API with impersonated credentials
        crm_service = build('cloudresourcemanager', 'v1', credentials=credentials)
        project_id = os.environ.get("PROJECT_ID")
        
        # Get IAM policy for the project
        policy_request = crm_service.projects().getIamPolicy(resource=project_id, body={})
        policy = policy_request.execute()

        # List roles and members
        roles_to_check = []
        for binding in policy.get('bindings', []):
            role = binding['role']
            members = binding.get('members', [])
            for member in members:
                if member.startswith('user:'):  # Only check user accounts
                    roles_to_check.append({'user': member, 'role': role})

        return roles_to_check

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return []

# Example usage
roles = list_iam_roles()
print(roles)
