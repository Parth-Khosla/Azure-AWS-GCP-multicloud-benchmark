#!/usr/bin/env python3
"""
Async AWS AMI Fetcher — Static HTML Version
Generates a clean, fully Python-rendered HTML table from fetched AMIs.
No JS, no lag — perfect for large datasets.
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
OUTPUT_JSON_FILE = Path("./aws_all_os_amis.json")
OUTPUT_HTML_FILE = Path("./aws_all_os_amis_static.html")

AMI_OWNERS = [
    "amazon",           # Amazon official
    "099720109477",     # Canonical (Ubuntu)
    "309956199498",     # Red Hat
    "679593333241",     # SUSE
    "801119661308",     # Microsoft
]

AMI_NAME_FILTERS = [
    "ubuntu/images/*",
    "amzn2-ami-hvm-*",
    "RHEL-*",
    "SLES-*",
    "Windows_Server-*",
]

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
                        is_throttled = isinstance(e, ClientError) and e.response.get("Error", {}).get("Code", "") in (
                            "Throttling", "RequestLimitExceeded", "ThrottlingException"
                        )
                        if attempt > MAX_RETRIES:
                            print(f"[WARN] Region={region} Owner={owner} pattern={pattern} failed after {attempt-1} retries: {e}")
                            break
                        backoff = BASE_BACKOFF * (BACKOFF_MULT ** (attempt - 1))
                        await asyncio.sleep(backoff + random.uniform(0, 0.3 * backoff))
    # Deduplicate by ImageId
    seen = {}
    for img in results:
        iid = img.get("ImageId")
        if not iid:
            continue
        if iid not in seen or img.get("CreationDate", "") > seen[iid].get("CreationDate", ""):
            seen[iid] = img
    return sorted(seen.values(), key=lambda x: x.get("CreationDate", ""), reverse=True)

async def worker(session, region, owner, name_filters, semaphore):
    amis = await describe_images_with_retry(session, region, owner, name_filters, semaphore)
    return {"region": region, "owner": owner, "amis": amis}

async def main():
    regions = load_regions()
    session = aioboto3.Session()
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    tasks = [worker(session, r, o, AMI_NAME_FILTERS, semaphore) for r in regions for o in AMI_OWNERS]

    print(f"⚡ Launching {len(tasks)} async tasks (max concurrency={MAX_CONCURRENCY})...")
    results = []
    for coro in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Fetching"):
        results.append(await coro)

    # Organize by region→owner
    organized = {}
    for r in results:
        organized.setdefault(r["region"], {})[r["owner"]] = r["amis"]

    save_json(OUTPUT_JSON_FILE, organized)
    print(f"✅ JSON saved -> {OUTPUT_JSON_FILE}")

    generate_static_html(organized, OUTPUT_HTML_FILE)
    print(f"✅ HTML saved -> {OUTPUT_HTML_FILE}")

def generate_static_html(data, path):
    """Render full static HTML using only Python (no JS)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AWS AMI Report</title>
<style>
body {{
  font-family: Arial, sans-serif;
  margin: 30px;
  background-color: #f8f8f8;
}}
h1, h2 {{
  color: #333;
}}
.region {{
  background-color: #0073bb;
  color: white;
  padding: 10px;
  border-radius: 6px;
}}
.owner {{
  background-color: #e3e3e3;
  padding: 6px 10px;
  margin-top: 10px;
  border-left: 4px solid #0073bb;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 40px;
}}
th, td {{
  padding: 8px 10px;
  border: 1px solid #ccc;
  text-align: left;
}}
th {{
  background-color: #0073bb;
  color: white;
  position: sticky;
  top: 0;
}}
tr:nth-child(even) {{
  background-color: #f2f2f2;
}}
.small {{
  font-size: 0.9em;
  color: #555;
}}
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
            html.append("""
            <table>
            <thead>
                <tr><th>ImageId</th><th>Name</th><th>CreationDate</th><th>Architecture</th><th>Description</th></tr>
            </thead>
            <tbody>
            """)
            for img in amis:
                html.append("<tr>" + "".join(
                    f"<td>{(img.get(k, '') or '').replace('<', '&lt;').replace('>', '&gt;')}</td>"
                    for k in ["ImageId", "Name", "CreationDate", "Architecture", "Description"]
                ) + "</tr>")
            html.append("</tbody></table>")

    html.append("</body></html>")

    path.write_text("\n".join(html), encoding="utf-8")

# =======================
if __name__ == "__main__":
    asyncio.run(main())
