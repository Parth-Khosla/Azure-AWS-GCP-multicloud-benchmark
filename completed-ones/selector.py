#!/usr/bin/env python3
"""
AWS Deployment Configurator — Final Version
Reads confirmed regions from selected_region.json,
validates AMI and VM selections, displays a summary table,
and saves the configuration to deployment_config.json.
"""

import json
import os
from tabulate import tabulate

# === File Paths ===
AMI_FILE = "aws_all_os_amis.json"
VM_FILE = "aws_all_vm_types.json"
REGIONS_FILE = "selected_regions.json"
DEPLOYMENT_CONFIG = "deployment_config.json"

# === Helper Functions ===

def load_json(path):
    """Safely load a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ File not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def find_ami_entry(ami_data, regions, key, value, arch):
    """
    Search AMI by Name or ImageId with architecture filter across all regions.
    Returns the first match found and its region.
    """
    for region in regions:
        region_data = ami_data.get(region, {})
        for owner, entries in region_data.items():
            for entry in entries:
                if entry.get(key) == value and entry.get("Architecture") == arch:
                    return region, entry
    return None, None

def find_vm_entry(vm_data, regions, instance_type):
    """
    Find instance type info within available regions.
    Returns the first match found and its region.
    """
    for region in regions:
        for region_entry in vm_data:
            if region_entry.get("region") == region:
                for inst in region_entry["instance_types"]:
                    if inst["InstanceType"] == instance_type:
                        return region, inst
    return None, None

def save_deployment_config(regions, ami_entry, vm_entry):
    """Save the confirmed configuration to deployment_config.json"""
    config = {
        "Regions": regions,
        "AMI": {
            "ImageId": ami_entry["ImageId"],
            "Name": ami_entry["Name"],
            "Architecture": ami_entry["Architecture"],
            "Description": ami_entry.get("Description", "N/A"),
            "CreationDate": ami_entry.get("CreationDate", "N/A")
        },
        "VM": {
            "InstanceType": vm_entry["InstanceType"],
            "vCPUs": vm_entry["vCPUs"],
            "MemoryMiB": vm_entry["MemoryMiB"],
            "Storage": vm_entry["Storage"],
            "NetworkPerformance": vm_entry["NetworkPerformance"],
            "FreeTier": vm_entry["FreeTier"]
        }
    }

    with open(DEPLOYMENT_CONFIG, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Deployment configuration saved to: {DEPLOYMENT_CONFIG}")

# === Main ===

def main():
    print("🚀 AWS Deployment Configurator\n")

    # Load data
    try:
        regions = load_json(REGIONS_FILE)
        print(f"🌍 Loaded confirmed regions: {regions}")
    except Exception as e:
        print(f"❌ Failed to load regions from {REGIONS_FILE}: {e}")
        return

    try:
        ami_data = load_json(AMI_FILE)
    except Exception as e:
        print(f"❌ Failed to load AMI data from {AMI_FILE}: {e}")
        return

    try:
        vm_data = load_json(VM_FILE)
    except Exception as e:
        print(f"❌ Failed to load VM data from {VM_FILE}: {e}")
        return

    # User inputs
    ami_input = input("\nEnter AMI Name or ImageId: ").strip()
    architecture = input("Enter Architecture (x86_64 / arm64): ").strip()
    instance_type = input("Enter VM Instance Type: ").strip()

    search_key = "ImageId" if ami_input.startswith("ami-") else "Name"

    # Find AMI and VM
    ami_region, ami_entry = find_ami_entry(ami_data, regions, search_key, ami_input, architecture)
    vm_region, vm_entry = find_vm_entry(vm_data, regions, instance_type)

    if not ami_entry:
        print("❌ No matching AMI found in any of the selected regions.")
        return
    if not vm_entry:
        print("❌ No matching VM type found in any of the selected regions.")
        return

    # Display summary table
    table = [
        ["Architecture", architecture],
        ["AMI Name", ami_entry["Name"]],
        ["Image ID", ami_entry["ImageId"]],
        ["Description", ami_entry.get("Description", "N/A")],
        ["Creation Date", ami_entry.get("CreationDate", "N/A")],
        ["Instance Type", vm_entry["InstanceType"]],
        ["vCPUs", vm_entry["vCPUs"]],
        ["Memory (MiB)", vm_entry["MemoryMiB"]],
        ["Storage", vm_entry["Storage"]],
        ["Network Performance", vm_entry["NetworkPerformance"]],
        ["Free Tier Eligible", "✅ Yes" if vm_entry["FreeTier"] else "❌ No"]
    ]

    print("\n📋 Deployment Summary:\n")
    print(tabulate(table, headers=["Property", "Value"], tablefmt="fancy_grid"))

    confirm = input("\nConfirm deployment configuration? (y/n): ").strip().lower()
    if confirm == "y":
        save_deployment_config(regions, ami_entry, vm_entry)
    else:
        print("❌ Deployment cancelled.")

if __name__ == "__main__":
    main()
