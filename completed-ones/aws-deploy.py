#!/usr/bin/env python3
"""
AWS Deployment Script (Clean Start & Resilient)
- Reads config.json
- Iterates over each region config
- Creates EC2 instances
- Measures deployment time
- Handles failures gracefully
- Deletes previous deployed_resources.json & deployment_times.json
- Saves:
  1. deployed_resources.json → VM ID, key, security group, etc.
  2. deployment_times.json → deployment start/end times
- Shows a summary table of all deployed instances at the end
"""

import boto3
import json
import time
import os
from datetime import datetime
from tabulate import tabulate
from botocore.exceptions import ClientError

CONFIG_FILE = "config.json"
RESOURCES_FILE = "deployed_resources.json"
TIMES_FILE = "deployment_times.json"

HARDCODED_PASSWORD = "Admin123!"  # Not recommended for production


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def append_json(path, new_entry):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(new_entry)
    save_json(path, data)


def display_summary_table(resources_file):
    if not os.path.exists(resources_file):
        print("⚠️ No deployed resources to display.")
        return

    with open(resources_file, "r") as f:
        data = json.load(f)

    if not data:
        print("⚠️ No deployed resources to display.")
        return

    table_data = [
        [
            d.get("Region"),
            d.get("InstanceId") or "FAILED",
            d.get("AMI"),
            d.get("InstanceType"),
            d.get("Architecture"),
            d.get("KeyName") or "-",
            d.get("SecurityGroupId") or "-",
            "❌" if d.get("Failed") else "✅"
        ]
        for d in data
    ]
    headers = ["Region", "InstanceId", "AMI", "InstanceType", "Architecture", "KeyName", "SG", "Status"]
    print("\n📋 Deployment Summary:\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def clean_previous_data():
    """Delete previous deployment JSON files if they exist"""
    for file in [RESOURCES_FILE, TIMES_FILE]:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ Deleted previous {file}")


def main():
    # Delete previous deployment data
    clean_previous_data()

    configs = load_config()
    print(f"🚀 Deploying to {len(configs)} region(s)")

    for cfg in configs:
        region = cfg["region"]
        ami_id = cfg["ami_id"]
        instance_type = cfg["instance_type"]
        architecture = cfg["architecture"]

        print(f"\n🌍 Deploying in {region} ...")
        ec2 = boto3.client("ec2", region_name=region)
        start_time = time.time()
        instance_id = None
        key_name = None
        key_path = None
        sg_id = None
        deploy_time = 0
        failed = False

        try:
            # Create Security Group
            sg_name = f"temp-sg-{int(start_time)}"
            sg = ec2.create_security_group(GroupName=sg_name, Description="Temporary SG for short-lived VM")
            sg_id = sg["GroupId"]

            # Allow SSH
            ec2.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[{
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                }]
            )

            # Create Key Pair
            key_name = f"temp-key-{int(start_time)}"
            key = ec2.create_key_pair(KeyName=key_name)
            key_material = key["KeyMaterial"]
            key_path = f"{key_name}.pem"
            with open(key_path, "w") as f:
                f.write(key_material)
            os.chmod(key_path, 0o400)

            # Launch EC2 instance
            response = ec2.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MinCount=1,
                MaxCount=1,
                KeyName=key_name,
                SecurityGroupIds=[sg_id]
            )
            instance = response["Instances"][0]
            instance_id = instance["InstanceId"]

            # Wait for running
            waiter = ec2.get_waiter("instance_running")
            waiter.wait(InstanceIds=[instance_id])

            end_time = time.time()
            deploy_time = end_time - start_time
            print(f"✅ Instance {instance_id} running in {deploy_time:.2f} seconds")

        except ClientError as e:
            print(f"⚠️ Deployment failed in {region}: {e}")
            failed = True
            end_time = time.time()
            deploy_time = 0

        # Save deployed resources
        deployed_data = {
            "Region": region,
            "InstanceId": instance_id,
            "AMI": ami_id,
            "InstanceType": instance_type,
            "Architecture": architecture,
            "KeyName": key_name if not failed else None,
            "KeyFile": key_path if not failed else None,
            "SecurityGroupId": sg_id if not failed else None,
            "Password": HARDCODED_PASSWORD if not failed else None,
            "Failed": failed
        }
        append_json(RESOURCES_FILE, deployed_data)

        # Save deployment times
        times_data = {
            "Region": region,
            "InstanceId": instance_id,
            "StartTime": datetime.fromtimestamp(start_time).isoformat(),
            "EndTime": datetime.fromtimestamp(end_time).isoformat(),
            "ElapsedSeconds": deploy_time
        }
        append_json(TIMES_FILE, times_data)

        print(f"📁 Deployment data saved to {RESOURCES_FILE} and {TIMES_FILE}")

    # Show summary table
    display_summary_table(RESOURCES_FILE)


if __name__ == "__main__":
    main()
