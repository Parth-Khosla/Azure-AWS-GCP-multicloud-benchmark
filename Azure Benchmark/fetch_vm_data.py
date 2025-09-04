import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.subscription import SubscriptionClient
from tqdm.asyncio import tqdm_asyncio  # async-friendly progress bar

# === Config ===
JSON_DIR = "JSON-data"
REGIONS_FILE = os.path.join(JSON_DIR, "selected_regions.json")
OUTPUT_FILE = os.path.join(JSON_DIR, "vm_data.json")

# Pinned images (10 Ubuntu, 10 Windows, 10 Other Linux)
PINNED_IMAGES = [
    # Ubuntu
    "Canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2",
    "Canonical:0001-com-ubuntu-server-focal:20_04-lts",
    "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2",
    "Canonical:0001-com-ubuntu-server-jammy:22_04-lts",
    "Canonical:0001-com-ubuntu-server-noble:24_04-lts-gen2",
    "Canonical:0001-com-ubuntu-server-noble:24_04-lts",
    "Canonical:0001-com-ubuntu-pro-jammy:22_04-lts-pro-gen2",
    "Canonical:0001-com-ubuntu-pro-focal:20_04-lts-pro-gen2",
    "Canonical:0001-com-ubuntu-server-bionic:18_04-lts-gen2",
    "Canonical:0001-com-ubuntu-pro-bionic:18_04-lts-pro-gen2",

    # Windows
    "MicrosoftWindowsServer:WindowsServer:2022-datacenter-azure-edition",
    "MicrosoftWindowsServer:WindowsServer:2022-datacenter-azure-edition-smalldisk",
    "MicrosoftWindowsServer:WindowsServer:2019-datacenter",
    "MicrosoftWindowsServer:WindowsServer:2019-datacenter-smalldisk",
    "MicrosoftWindowsServer:WindowsServer:2016-datacenter",
    "MicrosoftWindowsServer:WindowsServer:2016-datacenter-smalldisk",
    "MicrosoftWindowsServer:WindowsServer:2012-r2-datacenter",
    "MicrosoftWindowsServer:WindowsServer:2012-datacenter",
    "MicrosoftWindowsServer:WindowsServer:2019-datacenter-gensecond",
    "MicrosoftWindowsServer:WindowsServer:2022-datacenter-gensecond",

    # Other Linux
    "RedHat:RHEL:8-lvm-gen2",
    "RedHat:RHEL:9-lvm-gen2",
    "RedHat:RHEL:7-lvm",
    "SUSE:sles-15-sp5:gen2",
    "SUSE:sles-15-sp4:gen2",
    "Debian:debian-11:11-gen2",
    "Debian:debian-12:12-gen2",
    "OpenLogic:CentOS:7_9-gen2",
    "OpenLogic:CentOS:8_5-gen2",
    "Oracle:Oracle-Linux:8_7-gen2",
]


def get_credentials():
    """Return Azure credentials via Azure CLI login."""
    return AzureCliCredential()


def fetch_vm_sizes_sync(compute_client, region):
    """Blocking call to fetch VM sizes."""
    try:
        vm_sizes = list(compute_client.virtual_machine_sizes.list(region))
        return [
            {
                "name": size.name,
                "vcpus": size.number_of_cores,
                "memory_gb": size.memory_in_mb / 1024,
                "max_data_disks": size.max_data_disk_count,
            }
            for size in vm_sizes
        ]
    except Exception as e:
        print(f"[{region}] ❌ VM sizes failed: {e}")
        return []


def fetch_pinned_images_sync(compute_client, region):
    """Blocking call to fetch pinned images."""
    images = {}
    for pinned in PINNED_IMAGES:
        try:
            publisher, offer, sku = pinned.split(":")
            versions = list(
                compute_client.virtual_machine_images.list(
                    region, publisher, offer, sku
                )
            )
            if versions:
                latest = versions[-1]
                os_name = f"{publisher}-{offer}-{sku}"
                images[os_name] = {
                    "publisher": publisher,
                    "offer": offer,
                    "sku": sku,
                    "version": latest.name,
                }
        except Exception:
            # Skip if image not available in this region
            continue
    return images


def fetch_region_data_sync(credential, subscription_id, region):
    """Blocking region fetch (sizes + images)."""
    compute_client = ComputeManagementClient(credential, subscription_id)
    return region, {
        "sizes": fetch_vm_sizes_sync(compute_client, region),
        "images": fetch_pinned_images_sync(compute_client, region),
    }


async def fetch_all_regions(credential, subscription_id, regions):
    """Run region fetches concurrently using threads."""
    loop = asyncio.get_running_loop()
    all_results = {}

    with ThreadPoolExecutor(max_workers=10) as executor:  # adjust concurrency
        tasks = [
            loop.run_in_executor(
                executor, fetch_region_data_sync, credential, subscription_id, region
            )
            for region in regions
        ]
        for coro in tqdm_asyncio.as_completed(tasks, desc="Processing regions", unit="region"):
            region, data = await coro
            all_results[region] = data

    return all_results


async def main():
    os.makedirs(JSON_DIR, exist_ok=True)

    if os.path.exists(OUTPUT_FILE):
        print(f"🗑️ Removing old {OUTPUT_FILE} ...")
        os.remove(OUTPUT_FILE)

    if not os.path.exists(REGIONS_FILE):
        print(f"❌ {REGIONS_FILE} not found. Please run region selector first.")
        return
    with open(REGIONS_FILE) as f:
        regions = json.load(f)

    credential = get_credentials()
    subs_client = SubscriptionClient(credential)
    subscriptions = list(subs_client.subscriptions.list())
    if not subscriptions:
        print("❌ No subscriptions found in Azure account.")
        return
    subscription_id = subscriptions[0].subscription_id
    print(f"🔑 Using subscription: {subscription_id}")

    # Run async
    all_results = await fetch_all_regions(credential, subscription_id, regions)

    # Save JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"✅ Fresh VM data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
