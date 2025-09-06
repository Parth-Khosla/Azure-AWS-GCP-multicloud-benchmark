import json
import os

# Paths
DATA_DIR = os.path.join(os.getcwd(), "JSON-data")
VM_FILE = os.path.join(DATA_DIR, "vm_data.json")
REGIONS_FILE = os.path.join(DATA_DIR, "selected_regions.json")
DEPLOYMENT_FILE = os.path.join(DATA_DIR, "deployment_info.json")

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def main():
    # Load JSON data
    vm_data = load_json(VM_FILE)
    selected_regions = load_json(REGIONS_FILE)

    # Ask user input
    vm_name = input("Enter the VM size name: ").strip()
    os_image = input("Enter the OS image name: ").strip()

    # Check across all regions
    vm_details = None
    missing_regions = []
    for region in selected_regions:
        sizes = vm_data.get(region, {}).get("sizes", [])
        match = next((s for s in sizes if s["name"].lower() == vm_name.lower()), None)
        if not match:
            missing_regions.append(region)
        else:
            if not vm_details:
                vm_details = match  # Take the first region’s details (assuming consistent)

    if missing_regions:
        print(f"❌ VM size '{vm_name}' is NOT available in: {', '.join(missing_regions)}")
        return

    # Show details
    print("\n✅ VM found in all selected regions!")
    print(f"VM Name: {vm_name}")
    print(f"OS Image: {os_image}")
    print(f"vCPUs: {vm_details['vcpus']}")
    print(f"Memory (GB): {vm_details['memory_gb']}")
    print(f"Max Data Disks: {vm_details['max_data_disks']}")

    confirm = input("\nDo you want to save this configuration? (yes/no): ").strip().lower()
    if confirm in ["yes", "y"]:
        # Always overwrite deployment_info.json
        deployment_info = {
            "vm_config": {
                "vm_name": vm_name,
                "os_image": os_image,
                "vcpus": vm_details["vcpus"],
                "memory_gb": vm_details["memory_gb"],
                "max_data_disks": vm_details["max_data_disks"],
                "regions": selected_regions
            }
        }

        save_json(DEPLOYMENT_FILE, deployment_info)
        print(f"\n💾 Configuration saved (overwritten) to {DEPLOYMENT_FILE}")
    else:
        print("⚠️ Configuration not saved.")

if __name__ == "__main__":
    main()
