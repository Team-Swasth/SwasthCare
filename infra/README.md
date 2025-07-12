# Azure Infrastructure for SwasthCare

This folder contains Bicep files for deploying SwasthCare as an Azure Web App using Azure Developer CLI (azd).

## Resources Provisioned

- Azure App Service (Linux, Python)
- App Service Plan (Basic)
- Application Insights
- Log Analytics Workspace
- Azure Key Vault
- App Service Site Extension (Application Insights)

## Usage

1. Update `main.parameters.json` with your secrets and connection strings.
2. Run `azd up` from the project root to deploy all resources.
3. After deployment, configure Key Vault access policies for managed identity if needed.
