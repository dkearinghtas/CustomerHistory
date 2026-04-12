param(
    [string]$SubscriptionId = $Env:AZURE_SUBSCRIPTION_ID,
    [string]$ResourceGroup = $Env:AZURE_RESOURCE_GROUP,
    [string]$Location = $Env:AZURE_LOCATION,
    [string]$AppServicePlan = $Env:AZURE_APP_SERVICE_PLAN,
    [string]$WebAppName = $Env:AZURE_WEBAPP_NAME
)

if (-not (Get-Module -ListAvailable Az)) {
    Write-Error 'The Az PowerShell module is required. Install it with Install-Module Az -Scope CurrentUser.'
    return
}

if (-not $SubscriptionId) {
    $SubscriptionId = Read-Host 'Azure Subscription ID'
}
if (-not $ResourceGroup) {
    $ResourceGroup = Read-Host 'Resource group name (example: InvoiceViewer-rg)'
}
if (-not $Location) {
    $Location = Read-Host 'Azure region (example: westus)'
}
if (-not $AppServicePlan) {
    $AppServicePlan = Read-Host 'App Service plan name (example: InvoiceViewerPlan)'
}
if (-not $WebAppName) {
    $WebAppName = Read-Host 'Azure Web App name'
}

Write-Host "Using subscription: $SubscriptionId"
Write-Host "Resource group: $ResourceGroup"
Write-Host "Location: $Location"
Write-Host "App Service plan: $AppServicePlan"
Write-Host "Web App name: $WebAppName"

Write-Host 'Connecting to Azure...'
Connect-AzAccount | Out-Null

if ($SubscriptionId) {
    Set-AzContext -Subscription $SubscriptionId | Out-Null
}

Write-Host 'Creating resource group...'
New-AzResourceGroup -Name $ResourceGroup -Location $Location | Out-Null

Write-Host 'Creating App Service plan...'
$plan = Get-AzAppServicePlan -Name $AppServicePlan -ResourceGroupName $ResourceGroup -ErrorAction SilentlyContinue
if (-not $plan) {
    New-AzAppServicePlan -Name $AppServicePlan -ResourceGroupName $ResourceGroup -Location $Location -Tier Basic -WorkerSize Small -Linux | Out-Null
}

Write-Host 'Creating or updating Web App...'
$webapp = Get-AzWebApp -Name $WebAppName -ResourceGroupName $ResourceGroup -ErrorAction SilentlyContinue
if (-not $webapp) {
    New-AzWebApp -Name $WebAppName -ResourceGroupName $ResourceGroup -Location $Location -AppServicePlan $AppServicePlan -Runtime 'PYTHON:3.11' | Out-Null
} else {
    Set-AzWebApp -Name $WebAppName -ResourceGroupName $ResourceGroup -AppServicePlan $AppServicePlan | Out-Null
}

Write-Host 'Configuring default app settings...'
Set-AzWebApp -Name $WebAppName -ResourceGroupName $ResourceGroup -AppSettings @{ USE_LIVE_DATA = 'false' } | Out-Null

Write-Host 'Packaging app...'
$zipPath = Join-Path $PSScriptRoot 'InvoiceViewer.zip'
if (Test-Path $zipPath) { Remove-Item $zipPath }

$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    throw 'Python executable not found in PATH. Please install Python or ensure it is available in the current shell.'
}

$root = Join-Path $PSScriptRoot 'InvoiceViewer'
$script = @"
import os
import zipfile
root = r'$root'
zip_path = r'$zipPath'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirs, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            arcname = os.path.relpath(full, root)
            zf.write(full, arcname)
"@
$scriptFile = Join-Path $PSScriptRoot 'make_invoiceviewer_zip.py'
Set-Content -Path $scriptFile -Value $script
& $pythonExe $scriptFile
Remove-Item $scriptFile

Write-Host 'Deploying app package...'
Publish-AzWebApp -ResourceGroupName $ResourceGroup -Name $WebAppName -ArchivePath $zipPath | Out-Null

Write-Host "Deployment complete. Your app should be available at https://$WebAppName.azurewebsites.net"
