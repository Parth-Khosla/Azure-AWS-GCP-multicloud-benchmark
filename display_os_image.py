import json
import os
from tabulate import tabulate

def display_os_images(input_file="os_images.json", html_output_file="templates/os_images.html"):
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

    html_table = tabulate(table_data, headers=headers, tablefmt="html")

    styled_html = f"""
    <!DOCTYPE html>
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
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            tr:nth-child(even) {{background-color: #f2f2f2;}}
            tr:hover {{background-color: #ddd;}}
        </style>
    </head>
    <body>
        <h2>GCP Public OS Images</h2>
        {html_table}
    </body>
    </html>
    """

    os.makedirs("templates", exist_ok=True)
    with open(html_output_file, "w") as f:
        f.write(styled_html)

    print(f"\n📝 HTML exported to {html_output_file}")

if __name__ == "__main__":
    display_os_images()
