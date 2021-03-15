# Azure GHE E2E VM

## When to run

There are (soft) limitations on how often you can fire backup/restore operations in Azure. If you trigger too many, then you bump up against this limit, and subsequent pipelines will fail.
As such, we should limit the runs of this operation to only when the [Azure scripts](./azure_scripts) themselves change, when the tests change (list TBD), or when a manual trigger is fired with a specific variable set.

## Restoring the GHE Azure VM for E2E Testing

The scripts to [restore](./restore_azure_vm.sh) and [delete](./delete_azure_vm.ps1) VMs require several components to function properly

### Assumptions

* Existence of a `Service Principal` with the `Virtual Machine Contributor` role
* All relevant Azure CICD variables are set in the CI/CD variables section of Congregate
* The `GHE VM` is already setup with a resource group, containing the `VM`, a `vault`, and a `storage account`, and all items are in the same `region`
* The `GHE VM` has a `backup schedule`, and one backup has already been run (snapshot exists)
* There is a `service principal` that has the ability to backup and restore the VM
* A target `resource group` exists to store the restored VM and information, and it is in the same `region` as the *source* `resource group`
* A target `storage account` exists in the target `resource group`, and is also in the same `region` as the *source* `resource group`

### Variables

#### General

* AZURE_SUBSCRIPTION_SCOPE_ID: Scope for the Azure subscription we are working under

#### Service Principal

* AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID: The `appID` for the pre-existing service principal
* AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_PASSWORD: The `password` for the service principal
* AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_TENANT_ID: The `tenantID` for the pre-existing service principal

#### Snapshot source information

* AZURE_BACKUP_MANAGEMENT_TYPE: What type of Azure backup type are we performing?
* AZURE_VM_SOURCE_RESOURCE_GROUP: The `resource group` for the current "production" VM
* AZURE_VM_SOURCE_RECOVERY_VAULT: The `storage vault` in the `resource group` where the backup of the VM is stored. Note: As currently written, this needs to be in the `AZURE_VM_SOURCE_RESOURCE_GROUP`

#### Snapshot target information

* AZURE_VM_RESTORE_TARGET_RESOURCE_GROUP: The `resource group` that will be the target for the VM restore
* AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT: The short name of the `storage account` in the target resource group where backup data and templates will be stored
* AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT: A string of the form `/subscriptions/$AZURE_SUBSCRIPTION_SCOPE_ID/resourceGroups/E2E/providers/Microsoft.Storage/storageAccounts/$AZURE_VM_RESTORE_TARGET_STORAGE_ACCOUNT_SHORT`. The full path is required since we are restoring to a different storage account than the source resource group

## Removing the GHE Azure VM for E2E Testing

The `pwsh` [script](./delete_azure_vm.ps1) to remove the VM only requires that the host name be set in `Env:`. It figures the rest out on its own.

## Helpful Scripts

### Create a service principal

[Link](https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli)

```bash
export AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_NAME="congregate_ghe_vm_creator"
az ad sp create-for-rbac --name $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_NAME
```

### Assign VM work role to the service principal

```bash
# AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID from the create
export AZURE_VIRTUAL_MACHINE_CONTRIBUTOR_ROLE_NAME="9980e02c-c2be-4d73-94e8-173b1dc7cf3c"   # Or "Virtual Machine Contributor"
az role assignment create --assignee $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID --role $AZURE_VIRTUAL_MACHINE_CONTRIBUTOR_ROLE_NAME
```

### Reset password

```bash
az ad sp credential reset --name $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID
```

### Login as Service Principal

```bash
az login --service-principal --username $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID --password $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_PASSWORD --tenant $AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_TENANT_ID
```
