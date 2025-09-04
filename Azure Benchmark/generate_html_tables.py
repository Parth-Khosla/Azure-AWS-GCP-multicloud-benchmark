import json
import os
from tabulate import tabulate

JSON_DIR = "JSON-data"
TEMPLATE_DIR = "Templates"
INPUT_FILE = os.path.join(JSON_DIR, "vm_data.json")

CSS_STYLE = """
<style>
body {
    font-family: Arial, sans-serif;
    margin: 20px;
    background-color: #fafafa;
}
h1 {
    color: #333;
}
h2 {
    margin-top: 30px;
    color: #555;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
    font-size: 14px;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
}
th {
    background-color: #333;
    color: white;
}
tr:nth-child(even) {
    background-color: #f2f2f2;
}
</style>
"""


def make_html(region, data):
    """Generate HTML page for a region with VM sizes and images."""
    html = f"<html><head><title>{region} VM Data</title>{CSS_STYLE}</head><body>"
    html += f"<h1>Azure VM Data for {region}</h1>"

    # Sizes Table
    sizes = data.get("sizes", [])
    if isinstance(sizes, list) and sizes:
        headers = sizes[0].keys()
        rows = [list(item.values()) for item in sizes]
        html += "<h2>VM Sizes</h2>"
        html += tabulate(rows, headers, tablefmt="html")
    else:
        html += "<h2>VM Sizes</h2><p>No data available.</p>"

    # Images Table (dict → list of rows)
    images = data.get("images", {})
    if isinstance(images, dict) and images:
        rows = []
        for image_name, details in sorted(images.items()):
            row = {"name": image_name, **details}
            rows.append(row)

        headers = rows[0].keys()
        rows = [list(item.values()) for item in rows]

        html += "<h2>VM Images</h2>"
        html += tabulate(rows, headers, tablefmt="html")
    else:
        html += "<h2>VM Images</h2><p>No data available.</p>"

    html += "</body></html>"
    return html


def main():
    # Ensure Templates folder exists
    os.makedirs(TEMPLATE_DIR, exist_ok=True)

    # Load JSON data
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} not found. Run fetch script first.")
        return

    with open(INPUT_FILE) as f:
        vm_data = json.load(f)

    # Generate one HTML page per region
    for region, data in vm_data.items():
        output_path = os.path.join(TEMPLATE_DIR, f"{region}.html")
        html = make_html(region, data)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Created {output_path}")

    print(f"\n🎉 All region HTML pages saved in '{TEMPLATE_DIR}'")


if __name__ == "__main__":
    main()
