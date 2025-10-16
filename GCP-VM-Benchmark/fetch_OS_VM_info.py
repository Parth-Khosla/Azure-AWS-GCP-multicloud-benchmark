# fetch_all_os_vm_info_async.py
import asyncio
import json
from tqdm import tqdm
from tabulate import tabulate

# Major public image projects in GCP
IMAGE_PROJECTS = [
    "debian-cloud",
    "ubuntu-os-cloud",
    "centos-cloud",
    "rhel-cloud",
    "suse-cloud",
    "rocky-linux-cloud",
    "windows-cloud"
]

async def run_gcloud(cmd):
    """Run gcloud command asynchronously and return parsed JSON"""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{stderr.decode()}")
    return json.loads(stdout.decode()) if stdout else []

async def fetch_project_images(project):
    """Fetch image families from a single project"""
    data = await run_gcloud([
        "gcloud", "compute", "images", "list",
        f"--project={project}",
        "--format=json"
    ])
    return [
        {"family": img["family"], "project": img["project"]}
        for img in data if "family" in img
    ]

async def fetch_all_images():
    """Fetch image families from all projects in parallel"""
    images = []
    tasks = [fetch_project_images(p) for p in IMAGE_PROJECTS]

    # Use tqdm progress bar
    results = []
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching OS images"):
        result = await coro
        results.extend(result)

    # Deduplicate
    unique = {(i["family"], i["project"]): i for i in results}
    return list(unique.values())

async def fetch_machine_types(zone="us-central1-a"):
    """Fetch available machine types (sample zone)"""
    data = await run_gcloud([
        "gcloud", "compute", "machine-types", "list",
        f"--zones={zone}",
        "--format=json"
    ])
    return [
        {"name": m["name"], "cpus": m["guestCpus"], "memory_mb": m["memoryMb"]}
        for m in data
    ]

def save_to_json(images, machine_types):
    data = {
        "os_families": sorted(images, key=lambda x: (x["project"], x["family"])),
        "machine_types": machine_types
    }
    with open("os_vm_data.json", "w") as f:
        json.dump(data, f, indent=4)

def save_to_html(images, machine_types):
    html = "<html><body><h1>GCP OS Families & VM Types</h1>"

    # OS families
    os_table = tabulate(images, headers="keys", tablefmt="html")
    html += "<h2>OS Image Families</h2>" + os_table

    # VM types
    vm_table = tabulate(machine_types, headers="keys", tablefmt="html")
    html += "<h2>Machine Types (us-central1-a)</h2>" + vm_table

    html += "</body></html>"

    with open("os_vm_data.html", "w") as f:
        f.write(html)

async def main():
    print("⚡ Starting async fetch for OS families & VM types...\n")
    images = await fetch_all_images()
    machine_types = await fetch_machine_types()

    save_to_json(images, machine_types)
    save_to_html(images, machine_types)

    print("\n✅ OS families + VM types saved to os_vm_data.json and os_vm_data.html")

if __name__ == "__main__":
    asyncio.run(main())
