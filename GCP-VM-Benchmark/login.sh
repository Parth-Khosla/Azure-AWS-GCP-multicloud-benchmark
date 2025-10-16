
echo "🔑 Logging into gcloud CLI..."
gcloud auth login --no-launch-browser "$@"

echo "🔑 Setting up application default credentials..."
gcloud auth application-default login

echo "✅ Both CLI and ADC authentication completed."