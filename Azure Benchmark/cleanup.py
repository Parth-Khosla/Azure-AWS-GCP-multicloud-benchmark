import os
import json
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from tabulate import tabulate

# Paths
JSON_DATA_DIR = "JSON-data"
TO_CLEAN_FILE = os.path.join(JSON_DATA_DIR, "to_clean.json")

def get_credentials():
    return AzureCliCredential()

def list_subscriptions(credential):
    subscription_client = SubscriptionClient(credential)
    subscriptions = list(subscription_client.subscriptions.list())

    if not subscriptions:
        print("❌ No Azure subscriptions found. Please log in with 'az login'.")
        return {}

    headers = ["Option", "Subscription ID", "Name", "State"]
    rows = []
    sub_dict = {}

    for idx, sub in enumerate(subscriptions, 1):
        rows.append([str(idx), sub.subscription_id, sub.display_name, sub.state])
        sub_dict[str(idx)] = sub.subscription_id

    print("\nAvailable Subscriptions:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    return sub_dict

def delete_resource_group_async(credential, subscription_id, resource_group_name, location):
    resource_client = ResourceManagementClient(credential, subscription_id)
    try:
        print(f"🗑️ Sending delete request for resource group: {resource_group_name} (Location: {location}) ...")
        # Fire the delete request but DO NOT wait
        resource_client.resource_groups.begin_delete(resource_group_name)
        print(f"➡️ Delete initiated for {resource_group_name}")
    except Exception as e:
        print(f"⚠️ Failed to start deletion for {resource_group_name}: {e}")
        return False
    return True

def cleanup_resources(subscription_id):
    if not os.path.exists(TO_CLEAN_FILE):
        print(f"No {TO_CLEAN_FILE} file found. Nothing to clean.")
        return

    with open(TO_CLEAN_FILE, "r") as f:
        cleanup_data = json.load(f)

    if not cleanup_data:
        print("No resources to clean. File is empty.")
        return

    credential = get_credentials()
    remaining = []

    for entry in cleanup_data:
        success = delete_resource_group_async(
            credential,
            subscription_id,
            entry["resource_group"],
            entry.get("location", "unknown")
        )
        if not success:
            remaining.append(entry)

    # Since deletions are async, we don’t know yet which ones failed,
    # so we only keep entries that couldn’t be initiated
    with open(TO_CLEAN_FILE, "w") as f:
        json.dump(remaining, f, indent=4)

    if remaining:
        print("\n⚠️ Some delete requests could not be started. Check to_clean.json for details.")
    else:
        print("\n🚀 All delete requests sent. Resource groups will be cleaned up in the background by Azure.")

def main():
    credential = get_credentials()
    subscriptions_dict = list_subscriptions(credential)

    if not subscriptions_dict:
        return

    sub_choice = input("\nSelect subscription (enter number): ").strip()
    subscription_id = subscriptions_dict.get(sub_choice)

    if not subscription_id:
        print("❌ Invalid subscription choice.")
        return

    cleanup_resources(subscription_id)

if __name__ == "__main__":
    main()
