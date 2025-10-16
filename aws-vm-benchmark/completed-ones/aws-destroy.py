#!/usr/bin/env python3
"""
AWS Destroy Script (Updated for multi-region & failed deployments)
- Iterates through all entries in deployed_resources.json
- Deletes EC2 instances, Security Groups, and Key Pairs
- Skips failed instances gracefully
- Shows a summary table of destroyed resources
"""

import boto3
import json
import os
from botocore.exceptions import ClientError
from tabulate import tabulate

RESOURCES_FILE = "deployed_resources.json"


def load_resources():
    if not os.path.exists(RESOURCES_FILE):
        print(f"⚠️ {RESOURCES_FILE} not found. Nothing to destroy.")
        return []
    with open(RESOURCES_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Could not parse {RESOURCES_FILE}. Nothing to destroy.")
            return []


def destroy_resource(entry):
    region = entry.get("Region")
    instance_id = entry.get("InstanceId")
    sg_id = entry.get("SecurityGroupId")
    key_name = entry.get("KeyName")
    key_file = entry.get("KeyFile")
    failed = entry.get("Failed", False)

    print(f"\n🛑 Destroying resources in {region} ...")
    ec2 = boto3.client("ec2", region_name=region)
    destroyed_info = {"Region": region, "InstanceId": instance_id, "SG": sg_id, "KeyName": key_name, "Status": []}

    # Terminate instance (skip if InstanceId is None or failed)
    if instance_id and not failed:
        try:
            ec2.terminate_instances(InstanceIds=[instance_id])
            waiter = ec2.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=[instance_id])
            print(f"✅ Instance {instance_id} terminated")
            destroyed_info["Status"].append("Instance terminated")
        except ClientError as e:
            print(f"⚠️ Could not terminate instance {instance_id}: {e}")
            destroyed_info["Status"].append(f"Instance termination failed: {e}")
    else:
        destroyed_info["Status"].append("Instance skipped")

    # Delete Security Group (skip if None)
    if sg_id:
        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"✅ Security Group {sg_id} deleted")
            destroyed_info["Status"].append("SG deleted")
        except ClientError as e:
            print(f"⚠️ Could not delete SG {sg_id}: {e}")
            destroyed_info["Status"].append(f"SG deletion failed: {e}")
    else:
        destroyed_info["Status"].append("SG skipped")

    # Delete Key Pair (skip if None)
    if key_name:
        try:
            ec2.delete_key_pair(KeyName=key_name)
            if key_file and os.path.exists(key_file):
                os.remove(key_file)
            print(f"✅ Key Pair {key_name} and local key file deleted")
            destroyed_info["Status"].append("Key deleted")
        except ClientError as e:
            print(f"⚠️ Could not delete key {key_name}: {e}")
            destroyed_info["Status"].append(f"Key deletion failed: {e}")
    else:
        destroyed_info["Status"].append("Key skipped")

    return destroyed_info


def display_destroy_summary(destroyed_entries):
    if not destroyed_entries:
        print("⚠️ No resources destroyed.")
        return

    table_data = [
        [
            d["Region"],
            d["InstanceId"] or "FAILED",
            d["SG"] or "-",
            d["KeyName"] or "-",
            ", ".join(d["Status"])
        ]
        for d in destroyed_entries
    ]
    headers = ["Region", "InstanceId", "SG", "KeyName", "Status"]
    print("\n📋 Destroyed Resources Summary:\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def main():
    resources = load_resources()
    if not resources:
        return

    destroyed_entries = []
    for entry in resources:
        destroyed_info = destroy_resource(entry)
        destroyed_entries.append(destroyed_info)

    display_destroy_summary(destroyed_entries)

    # Optionally, clear the resources file
    os.remove(RESOURCES_FILE)
    print(f"\n🗑️ {RESOURCES_FILE} cleared. Cleanup complete!")


if __name__ == "__main__":
    main()
