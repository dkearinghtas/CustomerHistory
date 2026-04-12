# Clear startup file and restart app service to use Procfile
az webapp config set --name invoiceviewer-azdeploy001 --resource-group invoiceviewer-rg --startup-file ""
az webapp restart --name invoiceviewer-azdeploy001 --resource-group invoiceviewer-rg
