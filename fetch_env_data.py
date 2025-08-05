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

    # Simple CSS for styling tables
    css = """
    <style>
    body {
        font-family: Arial, sans-serif;
        margin: 40px;
        background-color: #f8f9fa;
        color: #212529;
    }
    h2 {
        color: #343a40;
        border-bottom: 2px solid #dee2e6;
        padding-bottom: 5px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 30px;
        background-color: #fff;
    }
    th, td {
        border: 1px solid #dee2e6;
        text-align: left;
        padding: 8px;
    }
    th {
        background-color: #e9ecef;
    }
    tr:nth-child(even) {
        background-color: #f1f3f5;
    }
    </style>
    """

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>GCP Environment Report</title>
        {css}
    </head>
    <body>
        <h1>GCP Environment Report</h1>
        <h2>Projects</h2>
        {df_projects.to_html(index=False, escape=False)}
        <h2>Enabled Services</h2>
        {df_services.to_html(index=False, escape=False)}
        <h2>gcloud Config</h2>
        {df_config.to_html(index=False, escape=False)}
    </body>
    </html>
    """

    with open(templates_dir / "report.html", "w") as f:
        f.write(html_content)

    print(f"✅ Report saved to '{templates_dir / 'report.html'}'")
