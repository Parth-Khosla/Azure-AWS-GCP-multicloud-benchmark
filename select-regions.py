# fetch_enabled_regions
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

# ==== REGION FETCHER ====
def fetch_enabled_regions():
    """Fetch only AWS regions that are enabled for this account"""
    ec2 = boto3.client("ec2")
    response = ec2.describe_regions(AllRegions=True)
    enabled = [
        r["RegionName"]
        for r in response["Regions"]
        if r["OptInStatus"] in ("opt-in-not-required", "opted-in")
    ]
    return enabled

# ==== FILE HELPERS ====
def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def generate_html(regions):
    """Generate a simple HTML page with checkboxes to select regions"""
    checkboxes = "".join(
        f'<label><input type="checkbox" value="{r}"> {r}</label><br>'
        for r in regions
    )
    html_content = f"""
    <html>
    <head>
        <title>AWS Region Selector</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            button {{
                background-color: #0073bb;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            }}
            button:hover {{ background-color: #005f99; }}
        </style>
    </head>
    <body>
        <h2>🌎 Select Enabled AWS Regions</h2>
        <p>Only regions enabled in your AWS account are shown.</p>
        {checkboxes}
        <br><button onclick="saveSelection()">Save Selection</button>
        <script>
        function saveSelection() {{
            let selected = [];
            document.querySelectorAll('input[type=checkbox]:checked')
                    .forEach(cb => selected.push(cb.value));

            if (selected.length === 0) {{
                alert("⚠️ Please select at least one region!");
                return;
            }}

            fetch('/save', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{regions: selected}})
            }})
            .then(res => res.json())
            .then(data => {{
                alert("✅ Saved on server! (" + data.file + ")");
            }})
            .catch(err => alert("❌ Error saving: " + err));
        }}
        </script>
    </body>
    </html>
    """
    with open(REGIONS_HTML_FILE, "w") as f:
        f.write(html_content)

# ==== FLASK APP ====
def launch_selector(port=5000, open_browser=True):
    """Start a small Flask app that lets the user select enabled regions"""
    app = Flask(__name__)

    regions = fetch_enabled_regions()
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

    def run_app():
        app.run(host="0.0.0.0", port=port, debug=False)

    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()

    if open_browser:
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:
            print(f"🌐 Open your browser at http://127.0.0.1:{port}")

    print(f"🚀 Region selector running on port {port}.")
    print(f"➡️  Open http://127.0.0.1:{port} to select regions.")
    print(f"🗂️  Selections will be saved to: {SELECTED_REGIONS_FILE}")
    return thread

# ==== MAIN ====
if __name__ == "__main__":
    thread = launch_selector()
    thread.join()
