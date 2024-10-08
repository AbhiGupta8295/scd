"""
Python script to list out all users in aws along with the frequently used roles
"""

import boto3
from datetime import datetime, timedelta
import csv

# Create a session using boto3
iam_client = boto3.client("iam")
# client = boto3.client("s3")
cloudtrail_client = boto3.client("cloudtrail")

# Define the time period for 3 months
time_threshold = datetime.now() - timedelta(days=90)


# Get all IAM users
def list_users():
    users = []
    try:
        paginator = iam_client.get_paginator("list_users")
        for response in paginator.paginate():
            users.extend(response["Users"])
    except Exception as e:
        print(f"Error retrieving users: {str(e)}")
    # print("users in list_users() ", users)
    return users


# List all roles assigned to a specific user (from policies or role assumptions)
def get_user_roles(user_name):
    roles = []
    try:
        # List attached user policies and look for roles within them
        response = iam_client.list_attached_user_policies(UserName=user_name)
        for policy in response["AttachedPolicies"]:
            # Get policy document and check for role usage
            policy_arn = policy["PolicyArn"]
            policy_doc = iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=iam_client.get_policy(PolicyArn=policy_arn)["Policy"][
                    "DefaultVersionId"
                ],
            )
            # Check if the policy document allows any roles (this is a simplified check)
            if "AssumeRole" in str(policy_doc):
                roles.append(policy_arn)  # Add the role if found
    except Exception as e:
        print(f"Error retrieving roles for user {user_name}: {str(e)}")
    # print("get_user_roles is roles :- ", roles)
    return roles


# Get CloudTrail events for role usage
def get_role_usage(role_name):
    last_used = None
    frequency = 0
    try:
        # Search CloudTrail events for role assumption
        response = cloudtrail_client.lookup_events(
            LookupAttributes=[
                {"AttributeKey": "EventName", "AttributeValue": "AssumeRole"}
            ],
            StartTime=time_threshold,  # Limit to past 3 months
            EndTime=datetime.now(),
        )
        for event in response["Events"]:
            if role_name in event["Resources"]:
                event_time = event["EventTime"]
                frequency += 1
                if not last_used or event_time > last_used:
                    last_used = event_time
    except Exception as e:
        print(f"Error retrieving CloudTrail events for role {role_name}: {str(e)}")
    # print("last_used is ", last_used)
    # print("frequency is ", frequency)
    return last_used, frequency


# Generate a report with user-role mapping, last usage, and frequency
def generate_user_role_report():
    report = []
    users = list_users()
    
    for user in users:
        user_name = user["UserName"]
        user_roles = get_user_roles(user_name)
        # print("user_role is : - ", user_roles)
        for role in user_roles:
            last_used, frequency = get_role_usage(role)
            report.append(
                {
                    "UserName": user_name,
                    "RoleName": role,
                    "LastUsed": last_used or "Never",
                    "UsageFrequency": frequency,
                }
            )
    
    # print("report with user-role mapping, last usage is :- ", report)
    return report


# Save the report to a CSV file
def save_report_to_csv(filename="user_role_report.csv"):
    # Generate the report
    report = generate_user_role_report()
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['UserName', 'RoleName', 'LastUsed', 'UsageFrequency'])
        writer.writeheader()
        for row in report:
            writer.writerow(row)
    print(f"Report saved to {filename}")
    return filename

# def list_s3():
#     response = client.list_buckets()
#     print("response",response)

if __name__ == "__main__":
    
    # Save the report to a CSV file
    save_report_to_csv("user_role_report.csv")
