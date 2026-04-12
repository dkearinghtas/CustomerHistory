# CustomerHistory
An easily deployable app to look up invoice history

## Azure App Service deployment

Use the included Azure PowerShell deployment script from the repository root.

Windows PowerShell:

```powershell
.\deploy-azure.ps1
```

macOS/Linux:

```bash
./deploy-azure.sh
```

These scripts create or update the resource group, App Service plan, and Web App, then deploy the `InvoiceViewer` folder.

`deploy-azure.ps1` now uses the PowerShell Az module instead of Azure CLI.

If you want GitHub Actions deployment instead, the workflow is available at `.github/workflows/azure-python-app.yml`.
