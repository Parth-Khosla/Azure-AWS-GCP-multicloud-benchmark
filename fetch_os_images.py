import asyncio
import json
from googleapiclient.discovery import build
from google.auth import default

async def fetch_images_for_project(project, compute):
    try:
        request = compute.images().list(project=project)
        images = []

        while request is not None:
            response = request.execute()
            for img in response.get("items", []):
                images.append({
                    "name": img.get("name"),
                    "family": img.get("family", "N/A"),
                    "creationTimestamp": img.get("creationTimestamp", "N/A"),
                    "selfLink": img.get("selfLink", "N/A")
                })
            request = compute.images().list_next(previous_request=request, previous_response=response)
        return project, images
    except Exception as e:
        return project, []

async def fetch_all_os_images_async(output_file="os_images.json"):
    credentials, _ = default()
    compute = build("compute", "v1", credentials=credentials)

    os_projects = [
        "debian-cloud", "ubuntu-os-cloud", "centos-cloud", "windows-cloud",
        "rhel-cloud", "suse-cloud", "opensuse-cloud", "rocky-linux-cloud"
    ]

    tasks = [fetch_images_for_project(project, compute) for project in os_projects]
    results = await asyncio.gather(*tasks)

    all_images = {project: images for project, images in results}

    with open(output_file, "w") as f:
        json.dump(all_images, f, indent=4)

def fetch_all_os_images(output_file="os_images.json"):
    asyncio.run(fetch_all_os_images_async(output_file))
