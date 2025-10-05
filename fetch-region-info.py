#!/usr/bin/env python3
"""
Async AWS AMI + VM Fetcher — Static HTML Version
Generates fully Python-rendered HTML tables for AMIs and instance types (VMs),
including free tier eligible VMs (t2.micro, t2.nano).
"""

import asyncio
import aioboto3
import json
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
from datetime import datetime
from botocore.exceptions import ClientError
import random

# ===== CONFIG =====
INPUT_REGIONS_FILE = Path("./selected_regions.json")
OUTPUT_AMI_JSON = Path("./aws_all_os_amis.json")
OUTPUT_VM_JSON = Path("./aws_all_vm_types.json")
OUTPUT_AMI_HTML = Path("./aws_all_os_amis_static.html")
OUTPUT_VM_HTML = Path("./aws_all_vm_types_static.html")

AMI_OWNERS = [
    "amazon",
    "099720109477",
    "309956199498",
    "679593333241",
    "801119661308",
]

AMI_NAME_FILTERS = [
    "ubuntu/images/*",
    "amzn2-ami-hvm-*",
    "RHEL-*",
    "SLES-*",
    "Windows_Server-*",
]

FREE_TIER_INSTANCES = ["t2.micro", "t2.nano", "t3.micro", "t3.nano"]

MAX_CONCURRENCY = 50
MAX_RETRIES = 6
BASE_BACKOFF = 0.5
BACKOFF_MULT = 2.0
COLLECT_FIELDS = ["ImageId", "Name", "CreationDate", "Architecture", "Description"]

# ==================

def load_regions():
    with open(INPUT_REGIONS_FILE) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

# ==== AMI FUNCTIONS ====
async def describe_images_with_retry(session, region, owner, name_filters, semaphore):
    results = []
    async with semaphore:
        async with session.client("ec2", region_name=region) as ec2:
            for pattern in name_filters:
                attempt = 0
                while True:
                    try:
                        params = {
                            "Owners": [owner],
                            "Filters": [
                                {"Name": "name", "Values": [pattern]},
                                {"Name": "state", "Values": ["available"]}
                            ]
                        }
                        resp = await ec2.describe_images(**params)
                        for img in resp.get("Images", []):
                            results.append({k: img.get(k, "") for k in COLLECT_FIELDS})
                        break
                    except Exception as e:
                        attempt += 1
                        if attempt > MAX_RETRIES:
                            print(f"[WARN] AMI fetch failed Region={region} Owner={owner} pattern={pattern}: {e}")
                            break
                        backoff = BASE_BACKOFF * (BACKOFF_MULT ** (attempt - 1))
                        await asyncio.sleep(backoff + random.uniform(0, 0.3 * backoff))
    # Deduplicate by ImageId
    seen = {}
    for img in results:
        iid = img.get("ImageId")
        if iid and (iid not in seen or img.get("CreationDate", "") > seen[iid].get("CreationDate", "")):
            seen[iid] = img
    return sorted(seen.values(), key=lambda x: x.get("CreationDate", ""), reverse=True)

async def fetch_ami_worker(session, region, owner, name_filters, semaphore):
    amis = await describe_images_with_retry(session, region, owner, name_filters, semaphore)
    return {"region": region, "owner": owner, "amis": amis}

# ==== VM FUNCTIONS ====
async def fetch_vm_types_worker(session, region, semaphore):
    async with semaphore:
        async with session.client("ec2", region_name=region) as ec2:
            attempt = 0
            while True:
                try:
                    resp = await ec2.describe_instance_types()
                    instance_types = []
                    for t in resp.get("InstanceTypes", []):
                        info = {
                            "InstanceType": t["InstanceType"],
                            "vCPUs": t.get("VCpuInfo", {}).get("DefaultVCpus", "N/A"),
                            "MemoryMiB": t.get("MemoryInfo", {}).get("SizeInMiB", "N/A"),
                            "Storage": "EBS only" if not t.get("InstanceStorageInfo") else "Local",
                            "NetworkPerformance": t.get("NetworkInfo", {}).get("NetworkPerformance", "N/A"),
                            "FreeTier": t["InstanceType"] in FREE_TIER_INSTANCES
                        }
                        instance_types.append(info)
                    # Ensure free tier VMs are included even if missing (just in case)
                    for ft in FREE_TIER_INSTANCES:
                        if ft not in [i["InstanceType"] for i in instance_types]:
                            instance_types.append({
                                "InstanceType": ft,
                                "vCPUs": "1",
                                "MemoryMiB": "512",
                                "Storage": "EBS only",
                                "NetworkPerformance": "Low to Moderate",
                                "FreeTier": True
                            })
                    return {"region": region, "instance_types": instance_types}
                except Exception as e:
                    attempt += 1
                    if attempt > MAX_RETRIES:
                        print(f"[WARN] VM fetch failed Region={region}: {e}")
                        return {"region": region, "instance_types": []}
                    backoff = BASE_BACKOFF * (BACKOFF_MULT ** (attempt - 1))
                    await asyncio.sleep(backoff + random.uniform(0, 0.3 * backoff))

# ==== HTML GENERATION ====
def generate_static_html_amis(data, path):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AWS AMI Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 30px; background-color: #f8f8f8; }}
h1, h2 {{ color: #333; }}
.region {{ background-color: #0073bb; color: white; padding: 10px; border-radius: 6px; }}
.owner {{ background-color: #e3e3e3; padding: 6px 10px; margin-top: 10px; border-left: 4px solid #0073bb; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; }}
th, td {{ padding: 8px 10px; border: 1px solid #ccc; text-align: left; }}
th {{ background-color: #0073bb; color: white; position: sticky; top: 0; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
.small {{ font-size: 0.9em; color: #555; }}
</style>
</head>
<body>
<h1>AWS AMI Data Report</h1>
<p class="small">Generated on {timestamp}</p>
"""]
    for region, owners in data.items():
        html.append(f'<h2 class="region">Region: {region}</h2>')
        for owner, amis in owners.items():
            html.append(f'<div class="owner">Owner: {owner} — {len(amis)} AMIs</div>')
            html.append("<table><thead><tr><th>ImageId</th><th>Name</th><th>CreationDate</th><th>Architecture</th><th>Description</th></tr></thead><tbody>")
            for img in amis:
                html.append("<tr>" + "".join(f"<td>{(img.get(k,'') or '').replace('<','&lt;').replace('>','&gt;')}</td>" for k in ["ImageId","Name","CreationDate","Architecture","Description"]) + "</tr>")
            html.append("</tbody></table>")
    html.append("</body></html>")
    path.write_text("\n".join(html), encoding="utf-8")

def generate_static_html_vms(data, path):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AWS VM Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 30px; background-color: #f8f8f8; }}
h1, h2 {{ color: #333; }}
.region {{ background-color: #28a745; color: white; padding: 10px; border-radius: 6px; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; }}
th, td {{ padding: 8px 10px; border: 1px solid #ccc; text-align: left; }}
th {{ background-color: #28a745; color: white; position: sticky; top: 0; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
.free {{ background-color: #ffeeba; }}
.small {{ font-size: 0.9em; color: #555; }}
</style>
</head>
<body>
<h1>AWS VM Types Report</h1>
<p class="small">Generated on {timestamp}</p>
"""]
    for region_data in data:
        region = region_data["region"]
        html.append(f'<h2 class="region">Region: {region}</h2>')
        html.append("<table><thead><tr><th>InstanceType</th><th>vCPUs</th><th>MemoryMiB</th><th>Storage</th><th>NetworkPerformance</th><th>FreeTier</th></tr></thead><tbody>")
        for vm in region_data["instance_types"]:
            cls = "free" if vm.get("FreeTier") else ""
            html.append(f"<tr class='{cls}'>" + "".join(f"<td>{vm.get(k,'')}</td>" for k in ["InstanceType","vCPUs","MemoryMiB","Storage","NetworkPerformance"]) + f"<td>{vm.get('FreeTier')}</td></tr>")
        html.append("</tbody></table>")
    html.append("</body></html>")
    path.write_text("\n".join(html), encoding="utf-8")

# ==== MAIN ====
async def main():
    regions = load_regions()
    session = aioboto3.Session()
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    # AMI tasks
    ami_tasks = [fetch_ami_worker(session, r, o, AMI_NAME_FILTERS, semaphore) for r in regions for o in AMI_OWNERS]
    print(f"⚡ Launching {len(ami_tasks)} AMI fetch tasks...")
    ami_results = []
    for coro in tqdm_asyncio.as_completed(ami_tasks, total=len(ami_tasks), desc="Fetching AMIs"):
        ami_results.append(await coro)
    organized_amis = {}
    for r in ami_results:
        organized_amis.setdefault(r["region"], {})[r["owner"]] = r["amis"]
    save_json(OUTPUT_AMI_JSON, organized_amis)
    generate_static_html_amis(organized_amis, OUTPUT_AMI_HTML)
    print(f"✅ AMI JSON & HTML saved -> {OUTPUT_AMI_JSON}, {OUTPUT_AMI_HTML}")

    # VM tasks
    vm_tasks = [fetch_vm_types_worker(session, r, semaphore) for r in regions]
    print(f"⚡ Launching {len(vm_tasks)} VM fetch tasks...")
    vm_results = []
    for coro in tqdm_asyncio.as_completed(vm_tasks, total=len(vm_tasks), desc="Fetching VMs"):
        vm_results.append(await coro)
    save_json(OUTPUT_VM_JSON, vm_results)
    generate_static_html_vms(vm_results, OUTPUT_VM_HTML)
    print(f"✅ VM JSON & HTML saved -> {OUTPUT_VM_JSON}, {OUTPUT_VM_HTML}")

if __name__ == "__main__":
    asyncio.run(main())
