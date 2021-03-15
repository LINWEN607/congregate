#!/bin/bash

# The only thing that is variable from run to run.
AZURE_RESTORED_VM_NAME="VM$CI_COMMIT_SHORT_SHA"

# Move to variable
AZURE_SOURCE_VM_HOST_NAME="$AZURE_SOURCE_VM_HOST_NAME"

# General account information
AZURE_SUBSCRIPTION_SCOPE_ID="$AZURE_SUBSCRIPTION_SCOPE_ID"

# Pre-created information for an existing service principal that has Virtual Machine Contributor permissions
AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID="$AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID"
AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_TENANT_ID="$AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_TENANT_ID"
# export AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_PASSWORD="SET IN CICD VARIABLES"

# Snapshot source information
AZURE_BACKUP_MANAGEMENT_TYPE="AzureIaasVM"
AZURE_VM_SOURCE_RESOURCE_GROUP="$AZURE_VM_SOURCE_RESOURCE_GROUP"
AZURE_VM_SOURCE_RECOVERY_VAULT="$AZURE_VM_SOURCE_RECOVERY_VAULT"

# Snapshot target information
AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP="$AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP"
AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT="$AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT"
# Since we are restoring to a different storage account, need the full path
AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT="/subscriptions/$AZURE_SUBSCRIPTION_SCOPE_ID/resourceGroups/$AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT"

echo "Showing variables"
echo "-----------------"
echo "AZURE_VM_SOURCE_RESOURCE_GROUP = ${AZURE_VM_SOURCE_RESOURCE_GROUP}"
echo "AZURE_VM_SOURCE_RECOVERY_VAULT = ${AZURE_VM_SOURCE_RECOVERY_VAULT}"
echo "AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT = ${AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT}"
echo "AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT = ${AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT}"

# Login as service principal
az login --service-principal --username $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID --password $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_PASSWORD --tenant $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_TENANT_ID

# The following two lines that determines the requirement for the souurce resource group and source vault to be linked
AZURE_CONTAINER_NAME=$(az backup container list --backup-management-type $AZURE_BACKUP_MANAGEMENT_TYPE --resource-group $AZURE_VM_SOURCE_RESOURCE_GROUP --vault-name $AZURE_VM_SOURCE_RECOVERY_VAULT --query [].properties.friendlyName --output tsv)
echo "Found AZURE_CONTAINER_NAME $AZURE_CONTAINER_NAME"

AZURE_ITEM_NAME=$(az backup item list --backup-management-type $AZURE_BACKUP_MANAGEMENT_TYPE --resource-group $AZURE_VM_SOURCE_RESOURCE_GROUP --vault-name $AZURE_VM_SOURCE_RECOVERY_VAULT --container-name $AZURE_CONTAINER_NAME --query [].properties.friendlyName --output tsv)
echo "Found AZURE_ITEM_NAME $AZURE_ITEM_NAME"

AZURE_RECOVERY_SNAPSHOT_NAME=$(az backup recoverypoint list --resource-group $AZURE_VM_SOURCE_RESOURCE_GROUP --vault-name $AZURE_VM_SOURCE_RECOVERY_VAULT --backup-management-type AzureIaasVM --container-name $AZURE_CONTAINER_NAME --item-name $AZURE_ITEM_NAME --query [0].name --output tsv)
echo "Found snapshot $AZURE_RECOVERY_SNAPSHOT_NAME."

AZURE_DISK_RESTORE_JOB_NAME=$(az backup restore restore-disks --resource-group $AZURE_VM_SOURCE_RESOURCE_GROUP --vault-name $AZURE_VM_SOURCE_RECOVERY_VAULT --container-name $AZURE_CONTAINER_NAME --item-name $AZURE_ITEM_NAME --rp-name $AZURE_RECOVERY_SNAPSHOT_NAME --storage-account $AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT --target-resource-group $AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP --restore-to-staging-storage-account --query name --output tsv)
echo "Started disk restore $AZURE_DISK_RESTORE_JOB_NAME"

stat=""
while [[ "$stat" != "Completed" && "$stat" != "CompletedWithWarnings" ]]
do
    echo "Waiting 60 seconds"
    sleep 60
    echo "Retrieving status"
    stat=$(az backup job list --resource-group $AZURE_VM_SOURCE_RESOURCE_GROUP --vault-name $AZURE_VM_SOURCE_RECOVERY_VAULT --query "[?name==\`$AZURE_DISK_RESTORE_JOB_NAME\`].{Status:properties.status}" --output tsv)    
    echo "Disk restore currently: $stat"
done
#   TODO: For completed with warnings, give the ability to check and restart from this point
#   Will probably require dumping variables to a cache or some storage mechanism

echo "AZURE_VM_SOURCE_RESOURCE_GROUP is $AZURE_VM_SOURCE_RESOURCE_GROUP"
echo "AZURE_VM_SOURCE_RECOVERY_VAULT is $AZURE_VM_SOURCE_RECOVERY_VAULT"
echo "AZURE_DISK_RESTORE_JOB_NAME is $AZURE_DISK_RESTORE_JOB_NAME"

AZURE_TEMPLATE_BLOB_URI=""
while [[ $AZURE_TEMPLATE_BLOB_URI == "" ]]
do
    AZURE_TEMPLATE_BLOB_URI=$(az backup job show --resource-group $AZURE_VM_SOURCE_RESOURCE_GROUP --vault-name $AZURE_VM_SOURCE_RECOVERY_VAULT --name $AZURE_DISK_RESTORE_JOB_NAME --query 'properties.extendedInfo.propertyBag."Template Blob Uri"' --output tsv)
done

echo "TEMPLATE BLOB URI is $AZURE_TEMPLATE_BLOB_URI"

IFS='/'
read -ra ADDR <<< "$AZURE_TEMPLATE_BLOB_URI"
AZURE_TEMPLATE_BLOB_CONTAINER_NAME=${ADDR[3]}
AZURE_TEMPLATE_BLOB_TEMPLATE_NAME=${ADDR[4]}
# AZURE_TEMPLATE_BLOB_TEMPLATE_NAME=${AZURE_TEMPLATE_BLOB_TEMPLATE_NAME::-1}
IFS=' '
echo "Container name is $AZURE_TEMPLATE_BLOB_CONTAINER_NAME"
echo "Template name is $AZURE_TEMPLATE_BLOB_TEMPLATE_NAME"

EXPIRE_TIME=$(date -u -d '30 minutes' +%Y-%m-%dT%H:%MZ)
echo "Token expire time is $EXPIRE_TIME"
CONNECTION=$(az storage account show-connection-string --resource-group $AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP --name $AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT --query connectionString)
echo "Connection information is $CONNECTION"
TOKEN=$(az storage blob generate-sas --container-name $AZURE_TEMPLATE_BLOB_CONTAINER_NAME --name $AZURE_TEMPLATE_BLOB_TEMPLATE_NAME --expiry $EXPIRE_TIME --permissions r --output tsv --connection-string $CONNECTION)
echo "Temporary token is $TOKEN"
URL=$(az storage blob url --container-name $AZURE_TEMPLATE_BLOB_CONTAINER_NAME --name $AZURE_TEMPLATE_BLOB_TEMPLATE_NAME --output tsv --connection-string $CONNECTION)
echo "Url is $URL"

echo "az deployment group create --resource-group $AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP --template-uri $URL?$TOKEN --parameters VirtualMachineName=\"${AZURE_RESTORED_VM_NAME}\""

# This should block until completion
DEPLOYMENT_GROUP_RESULTS=$(az deployment group create --name $AZURE_RESTORED_VM_NAME --resource-group $AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP --template-uri $URL?$TOKEN --parameters VirtualMachineName="${AZURE_RESTORED_VM_NAME}")
echo "$DEPLOYMENT_GROUP_RESULTS"

DEPLOYMENT_GROUP_STATUS=$(az deployment group show --resource-group $AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP --name $AZURE_RESTORED_VM_NAME --query properties.provisioningState --output tsv)

echo "Deployment group status is: $DEPLOYMENT_GROUP_STATUS"

if [ $DEPLOYMENT_GROUP_STATUS != "Succeeded" ]
then
    echo "Invalid deployment status. Exiting"
    exit 1
fi

PUBLIC_IP_ADDRESS_NAME=$(az deployment group show --resource-group $AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP --name $AZURE_RESTORED_VM_NAME --query properties.parameters.publicIpAddressName.value --output tsv)

IP_ADDRESS=$(az network public-ip show --resource-group $AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP --name "$PUBLIC_IP_ADDRESS_NAME" --query ipAddress --output tsv)

echo "$IP_ADDRESS"