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
