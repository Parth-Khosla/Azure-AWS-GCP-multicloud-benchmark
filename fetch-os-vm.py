# fetch_all_os_vm_info_async_aws.py
import asyncio
import json
from tqdm import tqdm
from tabulate import tabulate

# Regions to query (can be extended)
REGIONS = [
    "us-east-1", "us-west-1", "us-west-2", "eu-central-1"
]

# Common AMI owners (Amazon Linux, Canonical (Ubuntu), RedHat, SUSE, Microsoft)
AMI_OWNERS = [
    "amazon",           # Amazon-owned
    "099720109477",     # Canonical (Ubuntu)
    "309956199498",     # Red Hat
    "679593333241",     # SUSE
    "801119661308"      # Microsoft
]

async def run_aws(cmd):
    """Run AWS CLI command asynchronously and return parsed JSON"""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{stderr.decode()}")
    return json.loads(stdout.decode()) if stdout else []

async def fetch_ami_images(region):
    """Fetch AMIs for a region (filtered by owners)"""
    data = await run_aws([
        "aws", "ec2", "describe-images",
        "--owners", *AMI_OWNERS,
        "--region", region,
        "--query", "Images[*].[ImageId,Name,OwnerId,CreationDate]",
        "--output", "json"
    ])
    # Limit to avoid thousands of results (keep 50 per region)
    data = sorted(data, key=lambda x: x[3], reverse=True)[:50]
    return [
        {"region": region, "id": d[0], "name": d[1], "owner": d[2], "date": d[3]}
        for d in data
    ]

async def fetch_instance_types(region):
    """Fetch available instance types for a region"""
    data = await run_aws([
        "aws", "ec2", "describe-instance-types",
        "--region", region,
        "--query", "InstanceTypes[*].[InstanceType, VCpuInfo.DefaultVCpus, MemoryInfo.SizeInMiB]",
        "--output", "json"
    ])
    return [
        {"region": region, "type": d[0], "cpus": d[1], "memory_mb": d[2]}
        for d in data
    ]

async def fetch_all():
    """Fetch AMIs + instance types from all regions"""
    images, instances = [], []

    # Fetch AMIs
    tasks = [fetch_ami_images(r) for r in REGIONS]
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching AMIs"):
        res = await coro
        images.extend(res)

    # Fetch Instance Types
    tasks = [fetch_instance_types(r) for r in REGIONS]
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching Instance Types"):
        res = await coro
        instances.extend(res)

    return images, instances

def save_to_json(images, instances):
    """Save results into JSON"""
    data = {
        "ami_images": images,
        "instance_types": instances
    }
    with open("aws_os_vm_data.json", "w") as f:
        json.dump(data, f, indent=4)

def save_to_html(images, instances):
    """Save results into HTML (tables)"""
    html = "<html><body><h1>AWS AMIs & Instance Types</h1>"

    # AMI table
    ami_table = tabulate(images, headers="keys", tablefmt="html")
    html += "<h2>Sample AMIs (latest 50 per region)</h2>" + ami_table

    # Instance types table
    inst_table = tabulate(instances, headers="keys", tablefmt="html")
    html += "<h2>Instance Types</h2>" + inst_table

    html += "</body></html>"

    with open("aws_os_vm_data.html", "w") as f:
        f.write(html)

async def main():
    print("⚡ Starting async fetch for AWS AMIs & Instance Types...\n")
    images, instances = await fetch_all()

    save_to_json(images, instances)
    save_to_html(images, instances)

    print("\n✅ Data saved to aws_os_vm_data.json and aws_os_vm_data.html")

if __name__ == "__main__":
    asyncio.run(main())
