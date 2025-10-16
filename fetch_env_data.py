import subprocess
import json
from pathlib import Path
from tabulate import tabulate
from datetime import datetime

TEMPLATES_DIR = Path("templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

CSS_STYLE = """
<style>
    body {
        font-family: Arial, sans-serif;
        padding: 20px;
        background: #f9f9f9;
    }
    h2 {
        color: #333;
        margin-top: 40px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 40px;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 10px;
        text-align: left;
    }
    th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #fafafa;
    }
</style>
"""

def run_gcloud_cmd(cmd):
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(output)
    except subprocess.CalledProcessError:
        return {}

def export_html(tables, output_path):
    with open(output_path, "w") as f:
        f.write("<html><head><title>GCP Report</title>")
        f.write(CSS_STYLE)
        f.write("</head><body>\n")

        f.write(f"<h1>GCP Environment Report</h1><p>Generated at {datetime.now()}</p>\n")

        for title, headers, rows in tables:
            html_table = tabulate(rows, headers=headers, tablefmt="html")
            f.write(f"<h2>{title}</h2>\n{html_table}\n")

        f.write("</body></html>")
    print(f"💾 Styled HTML exported to {output_path}")

def main():
    output_json = Path("gcp_env_report.json")
    output_html = TEMPLATES_DIR / "report.html"

    config = run_gcloud_cmd(["gcloud", "config", "list", "--format=json"])
    current_project = config.get("core", {}).get("project", "")
    projects = run_gcloud_cmd(["gcloud", "projects", "list", "--format=json"])

    if current_project:
        services = run_gcloud_cmd([
            "gcloud", "services", "list", "--enabled",
            f"--project={current_project}", "--format=json"
        ])
    else:
        services = []

    report = {
        "projects": projects,
        "current_project_services": services,
        "gcloud_config": config
    }

    # Save JSON for backup/reference
    with open(output_json, "w") as f:
        json.dump(report, f, indent=2)

    # Prepare data for HTML
    tables = []

    if projects:
        project_rows = [[p["projectId"], p.get("name", ""), p.get("lifecycleState", "")] for p in projects]
        tables.append(("Projects", ["Project ID", "Name", "Lifecycle"], project_rows))

    if services:
        try:
            service_rows = [[s["config"]["name"], s["config"]["title"]] for s in services]
        except Exception:
            service_rows = [["[Error extracting service data]", ""]]
        tables.append(("Enabled Services", ["Service Name", "Title"], service_rows))

    export_html(tables, output_html)
    print(f"✅ Report saved to: {output_html.resolve()}")

if __name__ == "__main__":
    main()
