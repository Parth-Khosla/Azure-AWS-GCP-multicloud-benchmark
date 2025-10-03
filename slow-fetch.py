import asyncio
import boto3
import concurrent.futures
import json
from tqdm import tqdm
from tabulate import tabulate

# Regions to query
REGIONS = ["us-east-1", "us-west-1", "us-west-2", "ap-south-1"]

session = boto3.Session()

def fetch_ami_images(region):
    ec2 = session.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_images")
    images = []
    for page in paginator.paginate(Owners=["amazon"]):
        for img in page["Images"]:
            images.append({
                "region": region,
                "id": img["ImageId"],
                "name": img.get("Name", "N/A")
            })
    return images

def fetch_instance_types(region):
    ec2 = session.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_instance_types")
    types = []
    for page in paginator.paginate():
        for itype in page["InstanceTypes"]:
            types.append({
                "region": region,
                "type": itype["InstanceType"],
                "vcpu": itype["VCpuInfo"]["DefaultVCpus"],
                "memory": itype["MemoryInfo"]["SizeInMiB"]
            })
    return types

async def main():
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=32)

    print("⚡ Starting async fetch (All AMIs)...")

    # AMIs
    ami_tasks = [loop.run_in_executor(executor, fetch_ami_images, r) for r in REGIONS]
    amis = []
    for f in tqdm(asyncio.as_completed(ami_tasks), total=len(ami_tasks), desc="Fetching AMIs"):
        amis.extend(await f)

    # Instance types
    itype_tasks = [loop.run_in_executor(executor, fetch_instance_types, r) for r in REGIONS]
    instance_types = []
    for f in tqdm(asyncio.as_completed(itype_tasks), total=len(itype_tasks), desc="Fetching Instance Types"):
        instance_types.extend(await f)

    # Save
    data = {"amis": amis, "instance_types": instance_types}
    with open("aws_full_data.json", "w") as f:
        json.dump(data, f, indent=2)

    # Table
    table = [(a["region"], a["id"], a["name"]) for a in amis[:20]]
    print(tabulate(table, headers=["Region", "AMI ID", "Name"]))
    print("\n✅ Data saved to aws_full_data.json")

if __name__ == "__main__":
    asyncio.run(main())
