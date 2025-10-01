# delete_vms.py
import subprocess
import json

def delete_vms():
    with open("deployment_details.json") as f:
        deployment_details = json.load(f)

    for dep in deployment_details:
        vm_name = dep["vm_name"]
        zone = dep["zone"]

        print(f"Deleting {vm_name} in {zone}...")
        subprocess.run([
            "gcloud", "compute", "instances", "delete", vm_name,
            "--zone", zone, "--quiet"
        ], check=True)

    print("All VMs deleted successfully.")

if __name__ == "__main__":
    delete_vms()
