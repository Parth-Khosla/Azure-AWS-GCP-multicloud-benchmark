import json
from googleapiclient import discovery
from google.auth import default

def fetch_all_os_images(output_file="os_images.json"):
    credentials, _ = default()
    compute = discovery.build("compute", "v1", credentials=credentials)

    os_projects = [
        "debian-cloud",
        "ubuntu-os-cloud",
        "centos-cloud",
        "windows-cloud",
        "rhel-cloud",
        "suse-cloud",
        "opensuse-cloud",
        "rocky-linux-cloud"
    ]

    print("Fetching all available OS images (this may take a bit)...")
    all_images = {}

    for project in os_projects:
        try:
            print(f"Fetching from project: {project}")
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

            all_images[project] = images
        except Exception as e:
            print(f"Error fetching images from {project}: {e}")
            all_images[project] = []

    with open(output_file, "w") as f:
        json.dump(all_images, f, indent=4)

    print(f"\n🎉 All OS image data saved to: {output_file}")

if __name__ == "__main__":
    fetch_all_os_images()
