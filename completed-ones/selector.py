#!/usr/bin/env python3
"""
AWS Deployment Config Generator (Interactive)
---------------------------------------------
Reads regions from 'select_regions.json', gathers user inputs for
each region, and shows a tabular summary before saving to 'config.json'.
"""

import json
from pathlib import Path
from tabulate import tabulate

SELECTED_REGIONS_FILE = Path("selected_regions.json")
OUTPUT_FILE = Path("config.json")


def load_regions():
    """Load list of regions from select_regions.json"""
    if not SELECTED_REGIONS_FILE.exists():
        print(f"❌ Missing file: {SELECTED_REGIONS_FILE}")
        print("Please create a JSON file like: [\"us-east-1\", \"ap-south-1\"]")
        exit(1)
    try:
        with open(SELECTED_REGIONS_FILE, "r") as f:
            regions = json.load(f)
            if not isinstance(regions, list):
                raise ValueError("Invalid JSON format: must be a list of regions")
            return regions
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {SELECTED_REGIONS_FILE}: {e}")
        exit(1)


def ask_user_for_region_config(region):
    """Prompt user for deployment settings for a given region"""
    print(f"\n🗺️  Configuring deployment for region: {region}")
    ami_name = input("   → AMI Name (e.g., Ubuntu Server 24.04 LTS): ").strip()
    ami_id = input("   → AMI ID (region-specific): ").strip()
    instance_type = input("   → Instance Type (default: t2.micro): ").strip() or "t2.micro"

    while True:
        arch = input("   → Architecture [x86_64 / arm64] (default: x86_64): ").strip().lower() or "x86_64"
        if arch in ["x86_64", "arm64"]:
            break
        print("     ⚠️ Please choose either 'x86_64' or 'arm64'")

    return {
        "region": region,
        "ami_name": ami_name,
        "ami_id": ami_id,
        "instance_type": instance_type,
        "architecture": arch
    }


def display_summary(configs):
    """Display a table summarizing all region configurations"""
    table_data = [
        [
            c["region"],
            c["ami_name"],
            c["ami_id"],
            c["instance_type"],
            c["architecture"]
        ]
        for c in configs
    ]
    headers = ["Region", "AMI Name", "AMI ID", "Instance Type", "Architecture"]
    print("\n📋 Configuration Summary:\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def main():
    print("🚀 AWS Deployment Config Generator\n")

    regions = load_regions()
    print(f"📦 Loaded {len(regions)} regions: {', '.join(regions)}")

    configs = []
    for region in regions:
        region_config = ask_user_for_region_config(region)
        configs.append(region_config)

    # Show tabular summary
    display_summary(configs)

    # Ask for confirmation
    confirm = input("\n💾 Save this configuration to config.json? [Y/n]: ").strip().lower()
    if confirm not in ["", "y", "yes"]:
        print("❌ Operation cancelled. Nothing was saved.")
        return

    # Save the combined configuration
    with open(OUTPUT_FILE, "w") as f:
        json.dump(configs, f, indent=4)

    print(f"\n✅ Configuration saved to {OUTPUT_FILE.resolve()}")
    print("   You can now use this file to deploy region-specific AMIs.")


if __name__ == "__main__":
    main()
