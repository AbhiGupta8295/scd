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
