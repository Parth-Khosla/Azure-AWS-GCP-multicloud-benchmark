import os
import json
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from tabulate import tabulate
import datetime
import matplotlib.pyplot as plt

# Paths
JSON_DATA_DIR = "JSON-data"
DEPLOYMENT_LOG_FILE = os.path.join(JSON_DATA_DIR, "deployment_log.json")
TO_CLEAN_FILE = os.path.join(JSON_DATA_DIR, "to_clean.json")
DEPLOYMENT_PLOT_FILE = "deployment_time.png"

def get_credentials():
    return AzureCliCredential()

def validate_vm_name(name):
    valid_name = ''.join(c for c in name if c.isalnum() or c == '-')
    valid_name = valid_name[:15]
    
    if valid_name.isnumeric() or not valid_name[0].isalpha():
        valid_name = 'vm-' + valid_name
    
    return valid_name

def list_subscriptions(credential):
    subscription_client = SubscriptionClient(credential)
    subscriptions = list(subscription_client.subscriptions.list())
    
    headers = ["Option", "Subscription ID", "Name", "State"]
    rows = []
    
    for idx, sub in enumerate(subscriptions, 1):
        rows.append([str(idx), sub.subscription_id, sub.display_name, sub.state])
    
    print("\nAvailable Subscriptions:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return {str(idx): sub.subscription_id for idx, sub in enumerate(subscriptions, 1)}

def list_virtual_machines(credential, subscription_id):
    compute_client = ComputeManagementClient(credential, subscription_id)
    vms = list(compute_client.virtual_machines.list_all())
    
    headers = ["Name", "Resource Group", "Location", "Size", "State"]
    rows = []
    
    for vm in vms:
        rows.append([
            vm.name,
            vm.id.split('/')[4],
            vm.location,
            vm.hardware_profile.vm_size,
            vm.provisioning_state
        ])
    
    if rows:
        print("\nExisting Virtual Machines:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("\nNo existing virtual machines found.")

def create_infrastructure(
    credential,
    subscription_id,
    resource_group_name,
    location,
    vm_name,
    vm_size,
    vm_image
):
    resource_client = ResourceManagementClient(credential, subscription_id)
    network_client = NetworkManagementClient(credential, subscription_id)
    compute_client = ComputeManagementClient(credential, subscription_id)

    computer_name = validate_vm_name(vm_name)

    print(f"Creating Resource Group '{resource_group_name}'...")
    resource_client.resource_groups.create_or_update(
        resource_group_name,
        {"location": location}
    )

    vnet_name = f"{vm_name}-vnet"
    subnet_name = f"{vm_name}-subnet"
    ip_name = f"{vm_name}-ip"
    nic_name = f"{vm_name}-nic"

    print("Creating VNet and Subnet...")
    network_client.virtual_networks.begin_create_or_update(
        resource_group_name,
        vnet_name,
        {
            'location': location,
            'address_space': {'address_prefixes': ['10.0.0.0/16']},
            'subnets': [{'name': subnet_name, 'address_prefix': '10.0.0.0/24'}]
        }
    ).result()

    subnet = network_client.subnets.get(resource_group_name, vnet_name, subnet_name)

    print("Creating Public IP...")
    public_ip = network_client.public_ip_addresses.begin_create_or_update(
        resource_group_name,
        ip_name,
        {
            'location': location,
            'sku': {'name': 'Basic'},
            'public_ip_allocation_method': 'Dynamic',
            'public_ip_address_version': 'IPV4'
        }
    ).result()

    print("Creating Network Interface...")
    nic = network_client.network_interfaces.begin_create_or_update(
        resource_group_name,
        nic_name,
        {
            'location': location,
            'ip_configurations': [{
                'name': 'ipconfig1',
                'subnet': {'id': subnet.id},
                'public_ip_address': {'id': public_ip.id}
            }]
        }
    ).result()

    print(f"Creating VM '{vm_name}'...")

    # Start timing
    start_time = datetime.datetime.utcnow()
    print(f"Start Time (UTC): {start_time.isoformat()}")

    vm_parameters = {
        'location': location,
        'hardware_profile': {'vm_size': vm_size},
        'storage_profile': {
            'image_reference': vm_image,
            'os_disk': {
                'name': f'{vm_name}-disk',
                'caching': 'ReadWrite',
                'create_option': 'FromImage',
                'managed_disk': {'storage_account_type': 'Standard_LRS'}
            }
        },
        'os_profile': {
            'computer_name': computer_name,
            'admin_username': 'azureuser',
            'admin_password': 'Password123!'  # ⚠️ Replace securely in prod
        },
        'network_profile': {
            'network_interfaces': [{'id': nic.id}]
        }
    }

    compute_client.virtual_machines.begin_create_or_update(
        resource_group_name,
        vm_name,
        vm_parameters
    ).result()

    # End timing
    end_time = datetime.datetime.utcnow()
    duration = end_time - start_time

    print(f"End Time (UTC): {end_time.isoformat()}")
    print(f"Deployment Duration: {duration.total_seconds():.2f} seconds")

    log_deployment_time(vm_name, resource_group_name, location, start_time, end_time, duration)
    print(f"\nVM '{vm_name}' has been successfully created!")

def log_deployment_time(vm_name, resource_group_name, location, start_time, end_time, duration):
    log_entry = {
        "vm_name": vm_name,
        "resource_group": resource_group_name,
        "location": location,
        "start_time_utc": start_time.isoformat(),
        "end_time_utc": end_time.isoformat(),
        "duration_seconds": duration.total_seconds()
    }

    # Save to deployment_log.json
    if os.path.exists(DEPLOYMENT_LOG_FILE):
        with open(DEPLOYMENT_LOG_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(log_entry)

    with open(DEPLOYMENT_LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Deployment log saved to '{DEPLOYMENT_LOG_FILE}' 📝")

    # Track resource groups in to_clean.json
    if os.path.exists(TO_CLEAN_FILE):
        with open(TO_CLEAN_FILE, "r") as f:
            cleanup_data = json.load(f)
    else:
        cleanup_data = []

    cleanup_data.append({
        "resource_group": resource_group_name,
        "location": location,
        "vm_name": vm_name
    })

    with open(TO_CLEAN_FILE, "w") as f:
        json.dump(cleanup_data, f, indent=4)

    print(f"Cleanup info saved to '{TO_CLEAN_FILE}' 🗑️")

def deploy_to_regions(credential, subscription_id, regions, vm_config):
    for region in regions:
        region_rg_name = f"Bench-{region}"
        region_vm_name = f"{vm_config['vm_name']}-{region}"
        
        print(f"\nDeploying to region: {region}")
        create_infrastructure(
            credential=credential,
            subscription_id=subscription_id,
            resource_group_name=region_rg_name,
            location=region,
            vm_name=region_vm_name,
            vm_size=vm_config['vm_name'],  # maps to "Standard_B1s"
            vm_image={
                "publisher": "Canonical",
                "offer": "0001-com-ubuntu-server-focal",
                "sku": "20_04-lts",
                "version": "latest"
            } if isinstance(vm_config['os_image'], str) else vm_config['os_image']
        )

def main():
    # Clear previous logs
    if os.path.exists(DEPLOYMENT_LOG_FILE):
        os.remove(DEPLOYMENT_LOG_FILE)
    if os.path.exists(TO_CLEAN_FILE):
        os.remove(TO_CLEAN_FILE)

    print("Azure Multi-Region VM Deployment Script")
    print("=" * 40)

    # Load config from JSON-data/deployment_info.json
    config_path = os.path.join(JSON_DATA_DIR, "deployment_info.json")
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        return

    with open(config_path, "r") as f:
        config = json.load(f)

    vm_config = config["vm_config"]
    regions = vm_config["regions"]

    credential = get_credentials()
    subscriptions_dict = list_subscriptions(credential)
    if not subscriptions_dict:
        print("No subscriptions found. Please check your Azure login.")
        return

    sub_choice = input("\nSelect subscription (enter number): ")
    subscription_id = subscriptions_dict.get(sub_choice)
    if not subscription_id:
        print("Invalid subscription selection.")
        return

    list_virtual_machines(credential, subscription_id)

    deploy_to_regions(credential, subscription_id, regions, vm_config)

    # Plot results
    if os.path.exists(DEPLOYMENT_LOG_FILE):
        with open(DEPLOYMENT_LOG_FILE, 'r') as f:
            logs = json.load(f)

        vm_names = [entry['vm_name'] for entry in logs]
        durations = [entry['duration_seconds'] for entry in logs]

        plt.figure(figsize=(10, 6))
        plt.bar(vm_names, durations, color='skyblue')
        plt.title('VM Deployment Duration Comparison by Region', fontsize=14)
        plt.xlabel('VM Name', fontsize=12)
        plt.ylabel('Deployment Duration (seconds)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(DEPLOYMENT_PLOT_FILE)

    print("\nMulti-region deployment completed!")

if __name__ == "__main__":
    main()