import os
import json
from tabulate import tabulate

def display_os_images(input_file="os_images.json", html_output_file=None):
    with open(input_file, "r") as f:
        os_data = json.load(f)

    table_data = []
    headers = ["Project", "Image Name", "Family", "Creation Time"]

    for project, images in os_data.items():
        for info in images:
            table_data.append([
                project,
                info.get("name", "N/A"),
                info.get("family", "N/A"),
                info.get("creationTimestamp", "N/A")
            ])

    # Print to terminal
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Convert to HTML table
    html_table = tabulate(table_data, headers=headers, tablefmt="html")

    styled_html = f"""
    <html>
    <head>
        <title>GCP OS Images</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            tr:nth-child(even) {{background-color: #f2f2f2}}
            tr:hover {{background-color: #ddd;}}
        </style>
    </head>
    <body>
        <h2>GCP Public OS Images</h2>
        {html_table}
    </body>
    </html>
    """

    # Save to templates directory if no path provided
    if html_output_file is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(base_dir, "templates")
        os.makedirs(templates_dir, exist_ok=True)  # ✅ Ensure templates/ exists
        html_output_file = os.path.join(templates_dir, "os_images.html")

    with open(html_output_file, "w") as f:
        f.write(styled_html)

    print(f"\n📝 HTML exported to {html_output_file}")

if __name__ == "__main__":
    display_os_images()
