# create_config.py
import json

def create_config():
    config = {"deployments": []}

    while True:
        region = input("Enter a region for deployment (or 'done' to finish): ").strip()
        if region.lower() == "done":
            break
        image = input("Enter image (e.g. debian-12, ubuntu-2204-lts): ").strip()
        machine_type = input("Enter machine type (e.g. e2-micro, e2-medium): ").strip()

        config["deployments"].append({
            "region": region,
            "image": image,
            "machine_type": machine_type
        })

    with open("deployment_config.json", "w") as f:
        json.dump(config, f, indent=4)

    print("Config saved to deployment_config.json")

if __name__ == "__main__":
    create_config()
