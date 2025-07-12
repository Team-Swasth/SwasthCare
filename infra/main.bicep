// Main Bicep file for SwasthCare Azure Web App deployment
// This file provisions App Service, Application Insights, Log Analytics, Key Vault, and Site Extension

param environmentName string
param location string
param resourceGroupName string = 'rg-Sparkathon'
param DJANGO_SECRET_KEY securestring
param DATABASE_URL string
param AZURE_STORAGE_CONNECTION_STRING securestring

var resourcePrefix = environmentName
var resourceToken = uniqueString(subscription().id, resourceGroup().id, environmentName)
var appName = '${resourcePrefix}-${resourceToken}-webapp'
var appInsightsName = '${resourcePrefix}-${resourceToken}-ai'
var logAnalyticsName = '${resourcePrefix}-${resourceToken}-logs'
var keyVaultName = '${resourcePrefix}-${resourceToken}-kv'

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${appName}-plan'
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'linux'
}

resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${resourcePrefix}-${resourceToken}-identity'
  location: location
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: appName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      appSettings: [
        {
          name: 'DJANGO_SECRET_KEY'
          value: DJANGO_SECRET_KEY
        }
        {
          name: 'DATABASE_URL'
          value: DATABASE_URL
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: AZURE_STORAGE_CONNECTION_STRING
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
      ]
      cors: {
        allowedOrigins: [ '*' ]
        supportCredentials: false
      }
    }
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentity.id}': {}
    }
  }
  tags: {
    azd-service-name: 'SwasthCare'
    azd-env-name: environmentName
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: [] // Managed Identity will be configured post-deployment
    enableSoftDelete: true
    enablePurgeProtection: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
  }
}

resource siteExtension 'Microsoft.Web/sites/siteextensions@2022-03-01' = {
  name: '${appName}/Microsoft.ApplicationInsights.AzureWebSites'
  location: location
  properties: {}
}

output webAppName string = webApp.name
output appInsightsName string = appInsights.name
output logAnalyticsName string = logAnalytics.name
output keyVaultName string = keyVault.name
output RESOURCE_GROUP_ID string = resourceGroup().id
