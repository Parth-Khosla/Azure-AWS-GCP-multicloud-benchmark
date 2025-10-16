# deploy_vms.py
import subprocess
import json
import datetime
import uuid

def deploy_vms():
    with open("deployment_config.json") as f:
        config = json.load(f)

    deployment_details = []

    for dep in config["deployments"]:
        region = dep["region"]
        image = dep["image"]
        machine_type = dep["machine_type"]
        zone = f"{region}-a"  # pick zone "a" in the region

        vm_name = f"auto-vm-{uuid.uuid4().hex[:6]}"
        start_time = datetime.datetime.now()

        print(f"Deploying {vm_name} in {zone}...")

        subprocess.run([
            "gcloud", "compute", "instances", "create", vm_name,
            "--zone", zone,
            "--machine-type", machine_type,
            "--image-family", image,
            "--image-project", "debian-cloud" if "debian" in image else "ubuntu-os-cloud",
            "--boot-disk-size", "20GB"
        ], check=True)

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()

        deployment_details.append({
            "vm_name": vm_name,
            "region": region,
            "zone": zone,
            "image": image,
            "machine_type": machine_type,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "deployment_time_sec": duration
        })

    with open("deployment_details.json", "w") as f:
        json.dump(deployment_details, f, indent=4)

    print("Deployment complete. Details saved in deployment_details.json")

if __name__ == "__main__":
    deploy_vms()
