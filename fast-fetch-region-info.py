import asyncio
import aioboto3
import json
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio

# ==== CONFIG PATHS ====
INPUT_REGIONS_FILE = Path("./selected_regions.json")
OUTPUT_JSON_FILE = Path("./aws_fast_data.json")
OUTPUT_HTML_FILE = Path("./aws_fast_data.html")

async def fetch_region_data(session, region):
    """Fetch AMIs and instance types concurrently for a single region"""
    async with session.client("ec2", region_name=region) as ec2:
        amis_resp = await ec2.describe_images(Owners=["amazon"])
        amis = amis_resp.get("Images", [])[:10]  # trim

        types_resp = await ec2.describe_instance_types()
        types = types_resp.get("InstanceTypes", [])[:10]  # trim

    return {"region": region, "amis": amis, "instance_types": types}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def generate_html(data, path):
    rows = "".join(
        f"<tr><td>{d['region']}</td><td>{len(d['amis'])}</td><td>{len(d['instance_types'])}</td></tr>"
        for d in data
    )
    html = f"""
    <html><head><title>Fast AWS Data</title></head>
    <body>
      <h2>Fast Fetch Results</h2>
      <table border="1">
        <tr><th>Region</th><th>AMIs</th><th>Instance Types</th></tr>
        {rows}
      </table>
    </body></html>
    """
    with open(path, "w") as f:
        f.write(html)

async def main():
    with open(INPUT_REGIONS_FILE) as f:
        regions = json.load(f)

    print("⚡ Starting FAST fetch for selected regions...")

    # Use aioboto3 session
    session = aioboto3.Session()
    tasks = [fetch_region_data(session, r) for r in regions]

    results = []
    for coro in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Fetching regions"):
        res = await coro
        results.append(res)

    save_json(OUTPUT_JSON_FILE, results)
    generate_html(results, OUTPUT_HTML_FILE)
    print(f"\n✅ Fast fetch saved to {OUTPUT_JSON_FILE} and {OUTPUT_HTML_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
