#!/usr/bin/env bash
set -euo pipefail

subscription_id="${AZURE_SUBSCRIPTION_ID:-}"
resource_group="${AZURE_RESOURCE_GROUP:-}"
location="${AZURE_LOCATION:-westus}"
app_service_plan="${AZURE_APP_SERVICE_PLAN:-InvoiceViewerPlan}"
webapp_name="${AZURE_WEBAPP_NAME:-}"

if [[ -z "$subscription_id" ]]; then
  read -rp 'Azure Subscription ID: ' subscription_id
fi
if [[ -z "$resource_group" ]]; then
  read -rp 'Resource group name (example: InvoiceViewer-rg): ' resource_group
fi
if [[ -z "$webapp_name" ]]; then
  read -rp 'Azure Web App name: ' webapp_name
fi

echo "Using subscription: $subscription_id"
echo "Resource group: $resource_group"
echo "Location: $location"
echo "App Service plan: $app_service_plan"
echo "Web App name: $webapp_name"

az login >/dev/null
az account set --subscription "$subscription_id"
az group create --name "$resource_group" --location "$location"
az appservice plan create --name "$app_service_plan" --resource-group "$resource_group" --is-linux --sku B1
az webapp create --resource-group "$resource_group" --plan "$app_service_plan" --name "$webapp_name" --runtime "PYTHON:3.11"
az webapp config appsettings set --resource-group "$resource_group" --name "$webapp_name" --settings USE_LIVE_DATA=false

echo 'Packaging app...'
zip_file="$(pwd)/InvoiceViewer.zip"
rm -f "$zip_file"
if command -v python >/dev/null 2>&1; then
  python <<'PY'
import os
import zipfile
root = os.path.join(os.getcwd(), 'InvoiceViewer')
zip_path = os.path.join(os.getcwd(), 'InvoiceViewer.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirs, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            arcname = os.path.relpath(full, root)
            zf.write(full, arcname)
PY
elif command -v python3 >/dev/null 2>&1; then
  python3 <<'PY'
import os
import zipfile
root = os.path.join(os.getcwd(), 'InvoiceViewer')
zip_path = os.path.join(os.getcwd(), 'InvoiceViewer.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirs, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            arcname = os.path.relpath(full, root)
            zf.write(full, arcname)
PY
else
  cd InvoiceViewer
  zip -r "$zip_file" .
  cd - >/dev/null
fi

echo 'Deploying app package...'
az webapp deployment source config-zip --resource-group "$resource_group" --name "$webapp_name" --src "$zip_file"

echo "Deployment complete. Your app should be available at https://$webapp_name.azurewebsites.net"
