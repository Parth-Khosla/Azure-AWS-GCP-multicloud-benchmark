import subprocess
import json
import os
from pathlib import Path
import pandas as pd

def run_gcloud_cmd(cmd):
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(output)
    except subprocess.CalledProcessError:
        return {}

def main():
    output_file = Path("gcp_env_report.json")
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    config = run_gcloud_cmd(["gcloud", "config", "list", "--format=json"])
    current_project = config.get("core", {}).get("project", "")
    projects = run_gcloud_cmd(["gcloud", "projects", "list", "--format=json"])

    services = []
    if current_project:
        services = run_gcloud_cmd([
            "gcloud", "services", "list", "--enabled",
            f"--project={current_project}", "--format=json"
        ])

    report = {
        "projects": projects,
        "current_project_services": services,
        "gcloud_config": config
    }

    # Save JSON
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    # Convert to table and save as HTML
    df_projects = pd.DataFrame(projects)
    df_services = pd.DataFrame(services)
    df_config = pd.json_normalize(config)

    html_content = "<h2>Projects</h2>" + df_projects.to_html(index=False)
    html_content += "<h2>Enabled Services</h2>" + df_services.to_html(index=False)
    html_content += "<h2>gcloud Config</h2>" + df_config.to_html(index=False)

    with open(templates_dir / "report.html", "w") as f:
        f.write(html_content)

    print(f"✅ Report saved to '{templates_dir / 'report.html'}'")

if __name__ == "__main__":
    main()
