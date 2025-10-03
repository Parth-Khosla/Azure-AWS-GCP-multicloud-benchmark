import boto3
import json
from pathlib import Path
from tqdm import tqdm  # <-- added

# ==== CONFIG PATHS ====
INPUT_REGIONS_FILE = Path("./selected_regions.json")
OUTPUT_JSON_FILE = Path("./aws_slow_data.json")
OUTPUT_HTML_FILE = Path("./aws_slow_data.html")

def load_selected_regions():
    with open(INPUT_REGIONS_FILE) as f:
        return json.load(f)

def fetch_data(region):
    ec2 = boto3.client("ec2", region_name=region)
    amis = ec2.describe_images(Owners=["amazon"])["Images"]
    types = ec2.describe_instance_types()["InstanceTypes"]
    return {"region": region, "amis": amis[:10], "instance_types": types[:10]}  # trim

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def generate_html(data, path):
    rows = "".join(
        f"<tr><td>{d['region']}</td><td>{len(d['amis'])}</td><td>{len(d['instance_types'])}</td></tr>" 
        for d in data
    )
    html = f"""
    <html><head><title>Slow AWS Data</title></head>
    <body>
      <h2>Slow Fetch Results</h2>
      <table border="1">
        <tr><th>Region</th><th>AMIs</th><th>Instance Types</th></tr>
        {rows}
      </table>
    </body></html>
    """
    with open(path, "w") as f:
        f.write(html)

if __name__ == "__main__":
    regions = load_selected_regions()
    results = []
    print("⚡ Starting slow fetch for selected regions...")
    
    for region in tqdm(regions, desc="Fetching regions"):
        results.append(fetch_data(region))
    
    save_json(OUTPUT_JSON_FILE, results)
    generate_html(results, OUTPUT_HTML_FILE)
    print(f"\n✅ Slow fetch saved to {OUTPUT_JSON_FILE} and {OUTPUT_HTML_FILE}")
