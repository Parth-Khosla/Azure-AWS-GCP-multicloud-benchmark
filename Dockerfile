FROM python:3.11-slim

# Install required dependencies
RUN apt-get update && apt-get install -y curl gnupg apt-transport-https ca-certificates

# Install gcloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && apt-get install -y google-cloud-sdk

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Set default command to run Flask app
CMD ["python", "app.py"]
