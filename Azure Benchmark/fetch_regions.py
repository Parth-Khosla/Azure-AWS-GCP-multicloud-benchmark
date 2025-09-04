import subprocess
import json
import os
import logging
from tabulate import tabulate

OUTPUT_DIR = "JSON-data"
TEMPLATES_DIR = "Templates"
LOG_DIR = "logs"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "azure_fetch.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="a")
    ]
)

CSS_STYLE = """
<style>
body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
h1 { color: #333; }
table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #0078D4; color: white; }
tr:nth-child(even) { background-color: #f2f2f2; }
</style>
"""

def main():
    logging.info("Fetching Azure regions...")
    cmd = ["az", "account", "list-locations", "--output", "json"]
    regions = json.loads(subprocess.check_output(cmd, text=True))

    output_file = os.path.join(OUTPUT_DIR, "regions.json")
    with open(output_file, "w") as f:
        json.dump(regions, f, indent=2)

    logging.info(f"✅ Saved Azure regions to {output_file}")

    # Generate HTML
    html = f"<html><head>{CSS_STYLE}</head><body>"
    html += "<h1>Available Azure Regions</h1>"

    headers = ["name", "displayName", "regionalDisplayName"]
    table = [[r.get("name", ""), r.get("displayName", ""), r.get("regionalDisplayName", "")] for r in regions]
    html += tabulate(table, headers=headers, tablefmt="html")

    html += "</body></html>"

    html_file = os.path.join(TEMPLATES_DIR, "regions.html")
    with open(html_file, "w") as f:
        f.write(html)

    logging.info(f"✅ Regions HTML saved to {html_file}")

if __name__ == "__main__":
    main()
