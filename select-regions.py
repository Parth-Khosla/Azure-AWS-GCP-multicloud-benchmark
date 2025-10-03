import boto3
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
import threading
import webbrowser

# ==== CONFIG PATHS ====
OUTPUT_DIR = Path(".")
ALL_REGIONS_FILE = OUTPUT_DIR / "all_regions.json"
SELECTED_REGIONS_FILE = OUTPUT_DIR / "selected_regions.json"
REGIONS_HTML_FILE = OUTPUT_DIR / "regions.html"

def fetch_regions():
    ec2 = boto3.client("ec2")
    response = ec2.describe_regions(AllRegions=True)
    return [r["RegionName"] for r in response["Regions"]]

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def generate_html(regions):
    checkboxes = "".join(
        f'<label><input type="checkbox" value="{r}"> {r}</label><br>'
        for r in regions
    )
    html_content = f"""
    <html>
    <head><title>AWS Region Selector</title></head>
    <body>
        <h2>Select AWS Regions</h2>
        {checkboxes}
        <br>
        <button onclick="saveSelection()">Save Selection</button>
        <script>
        function saveSelection() {{
            let selected = [];
            document.querySelectorAll('input[type=checkbox]:checked').forEach(cb => selected.push(cb.value));
            if (selected.length === 0) {{ alert("Select at least one region"); return; }}

            fetch('/save', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{regions: selected}})
            }}).then(res => res.json())
              .then(data => alert("✅ Saved on server!"))
              .catch(err => alert("❌ Error saving: " + err));
        }}
        </script>
    </body>
    </html>
    """
    with open(REGIONS_HTML_FILE, "w") as f:
        f.write(html_content)

def launch_selector(port=5000, open_browser=True):
    """Start a temporary Flask app to select AWS regions"""
    app = Flask(__name__)
    regions = fetch_regions()
    save_json(ALL_REGIONS_FILE, regions)
    generate_html(regions)

    @app.route("/")
    def serve_html():
        return send_from_directory(".", REGIONS_HTML_FILE.name)

    @app.route("/save", methods=["POST"])
    def save_selection():
        data = request.json
        selected = data.get("regions", [])
        save_json(SELECTED_REGIONS_FILE, selected)
        return jsonify({"saved": selected, "file": str(SELECTED_REGIONS_FILE)})

    # Run Flask in a separate thread so it can be called from other scripts
    def run_app():
        app.run(host="0.0.0.0", port=port, debug=False)

    thread = threading.Thread(target=run_app)
    thread.daemon = True
    thread.start()

    if open_browser:
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:
            print(f"Open your browser and visit http://127.0.0.1:{port} to select regions")

    print(f"🚀 Region selector running at port {port}, select regions to save to {SELECTED_REGIONS_FILE}")
    return thread  # returns the Flask thread if caller wants to join/stop later


if __name__ == "__main__":
    # Example usage: start the selector and let user interact
    thread = launch_selector()
    thread.join()
