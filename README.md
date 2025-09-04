# Multi Region Multi Cloud Benchmark

## Aim
The purpose of this project is to benchmark multiple cloud resources simultaneously, or individual cloud platforms across multiple regions. The primary focus is on **Azure**, **AWS**, and **GCP**.

---

## Current Status

### Azure Module
- Can fetch **VM details** and display them in a **HTML format**.  
- Uses **JSON files** instead of databases to store data.  
- Implements **logging** to track errors if they occur.  

### Features in Progress
- **Deployment Script**: Uses Terraform (or similar) to deploy VMs using a JSON configuration file.  
- **VM Selector**: Allows users to input the required VM size and image, storing selections in a deployment JSON file.  
- Deployment script will **measure deployment time** and store created resources in another JSON file.  
- **Benchmark Script**: Benchmarks the deployed VM performance.  
- **Deletion Script**: Deletes resources created based on the deployment JSON file.  
- **Visualization**: Ability to visualize data in graphical form.  
- **Dockerization**: Make the application runnable on all platforms.  
- **Modular Flask App**: `app.py` will orchestrate all scripts in a modular fashion.

---

## Up Next
- **AWS Benchmark**: Implement benchmark functionality for AWS.  
- **GCP Benchmark**: Implement benchmark functionality for GCP.

---

## Tech Stack
- **Backend**: Python, Flask  
- **Data Storage**: JSON files  
- **Infrastructure as Code**: Terraform (or similar)  
- **Containerization**: Docker  
- **Visualization**: (Pending: matplotlib, plotly, or similar)
- **CLI tools**: Azure CLI, AWS CLI, GCP CLI

---

## How to Run (Azure Module Example)
1. Need to install Azure CLI tool and login using
    ```
    az login
2. Clone the repository:  
   ```bash
   git clone <repo-url>
   cd multi-region-multi-cloud-benchmark
3. Install requirements.txt
    ```bash
    pip install -r requirements.txt
4. Run the flask app
    ```bash
    python app.py
5. access the app on appropriate port(port 80 for now)

# Furture improvements

- Expand benchmark coverage for AWS and GCP.

- Add full automation for deployment, benchmarking, and deletion of VMs.

- Enhance visualization capabilities with interactive charts.

- Improve modularity and Docker support for cross-platform execution.

# Notes

- Currently, data is stored in JSON files for simplicity. Future versions may integrate databases for scalability.

- Error logging is implemented to facilitate debugging.


---

## 👤 Made By

**Parth Khosla**  

- 📧 Email: [khosla.parth@gmail.com](mailto:khosla.parth@gmail.com)  
- 💼 LinkedIn: [linkedin.com/in/parth-khosla](https://www.linkedin.com/in/parth-khosla/)  
- 🌐 GitHub: [github.com/parth-khosla](https://github.com/parth-khosla)  

---
