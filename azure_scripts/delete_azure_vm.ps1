Write-Host -ForegroundColor Cyan 'Setting PSRepository'
Set-PSRepository -Name PSGallery

Write-Host -ForegroundColor Cyan 'Installing Az module'
Install-Module -Name Az -AllowClobber -Scope CurrentUser -Force -AcceptLicense

Write-Host -ForegroundColor Cyan 'Importing Az.Compute module'
Import-Module -Name Az.Compute

$User = "$Env:AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_APP_ID"
Write-Host -ForegroundColor Cyan 'Using user $User'

$PWord = ConvertTo-SecureString -String "$Env:AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_PASSWORD" -AsPlainText -Force
$Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord

Write-Host -ForegroundColor Cyan 'Connecting with tenant $Env:AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_TENANT_ID'
Connect-AzAccount -Credential $Credential -Tenant "$Env:AZURE_GHE_VM_CREATOR_SERVICE_PRINCIPAL_TENANT_ID" -ServicePrincipal

Write-Host -ForegroundColor Cyan "Displaying current AzContext"
Get-AzContext

$VMName = 'VM' + (Get-ChildItem -Path Env:CI_COMMIT_SHORT_SHA).value
Write-Host -ForegroundColor Cyan 'VMName -' $VMName

$vm = Get-AzVm -Name $VMName
$data_disk_array = @()

if ($vm) {
    $RGName = $vm.ResourceGroupName
    Write-Host -ForegroundColor Cyan 'Resource Group Name is identified as-' $RGName
    $diagSa = [regex]::match($vm.DiagnosticsProfile.bootDiagnostics.storageUri, '^http[s]?://(.+?)\.').groups[1].value
    Write-Host -ForegroundColor Cyan 'Marking Disks for deletion...'
    $tags = @{"VMName" = $VMName; "Delete Ready" = "Yes" }
    $osDiskName = $vm.StorageProfile.OSDisk.Name
    Write-Host -ForegroundColor Cyan "Located OS Disk: $osDiskName"
    $datadisks = $vm.StorageProfile.DataDisks
    Write-Host -ForegroundColor Cyan "Located Data Disk(s): $datadisks"
    $ResourceID = (Get-Azdisk -Name $osDiskName).Id
    $OSDiskResourceID = $ResourceID
    $OSDiskName = (Get-Azdisk)
    Write-Host -ForegroundColor Cyan "OS Disk ResourceID: $ResourceID"
    Write-Host -ForegroundColor Cyan "Tagging resource $ResourceID with tags $tags"
    # For whatever reason, this currently fails in a pipeline, and I can't see why.
    # Later, I force a remove of the OS Disk based on the same ResourceID and it works
    # So it just can't find it for the tagging
    # New-AzTag -ResourceId $ResourceID -Tag $tags
    if ($vm.StorageProfile.DataDisks.Count -gt 0) {
        foreach ($datadisks in $vm.StorageProfile.DataDisks) {
            $datadiskname = $datadisks.name            
            $ResourceID = (Get-Azdisk -Name $datadiskname).Id
            # Write-Host -ForegroundColor Cyan "Tagging disk: $datadiskname with ResourceID: $ResourceID"
            Write-Host -ForegroundColor Cyan "Adding disk: $datadiskname with ResourceID: $ResourceID to the data disk array"
            $data_disk_array += "$ResourceID"
            # New-AzTag -ResourceId $ResourceID -Tag $tags | Out-Null
        }
    }
    if ($vm.Name.Length -gt 9) {
        $i = 9
    }
    else {
        $i = $vm.Name.Length - 1
    }
    $azResourceParams = @{
        'ResourceName'      = $VMName
        'ResourceType'      = 'Microsoft.Compute/virtualMachines'
        'ResourceGroupName' = $RGName
    }
    $vmResource = Get-AzResource @azResourceParams
    $vmId = $vmResource.Properties.VmId
    $diagContainerName = ('bootdiagnostics-{0}-{1}' -f $vm.Name.ToLower().Substring(0, $i), $vmId)
    $diagSaRg = (Get-AzStorageAccount | Where-Object { $_.StorageAccountName -eq $diagSa }).ResourceGroupName
    $saParams = @{
        'ResourceGroupName' = $diagSaRg
        'Name'              = $diagSa
    }
    Write-Host -ForegroundColor Cyan 'Removing Boot Diagnostic disk..'
    if ($diagSa) {
        Get-AzStorageAccount @saParams | Get-AzStorageContainer | Where-Object { $_.Name -eq $diagContainerName } | Remove-AzStorageContainer -Force
    }
    else {
        Write-Host -ForegroundColor Green "No Boot Diagnostics Disk found attached to the VM!"
    }
    Write-Host -ForegroundColor Cyan 'Removing Virtual Machine-' $VMName 'in Resource Group-'$RGName '...'
    $null = $vm | Remove-AzVM -Force
    Write-Host -ForegroundColor Cyan 'Removing Network Interface Cards, Public IP Address(s) used by the VM...'
    foreach ($nicUri in $vm.NetworkProfile.NetworkInterfaces.Id) {
        $nic = Get-AzNetworkInterface -ResourceGroupName $vm.ResourceGroupName -Name $nicUri.Split('/')[-1]
        Remove-AzNetworkInterface -Name $nic.Name -ResourceGroupName $vm.ResourceGroupName -Force
        foreach ($ipConfig in $nic.IpConfigurations) {
            if ($null -ne $ipConfig.PublicIpAddress) {
                Remove-AzPublicIpAddress -ResourceGroupName $vm.ResourceGroupName -Name $ipConfig.PublicIpAddress.Id.Split('/')[-1] -Force
            }
        }
    }
    Write-Host -ForegroundColor Cyan 'Removing OS disk and Data Disk(s) used by the VM..'
    # Get-AzResource -tag $tags | Where-Object { $_.resourcegroupname -eq $RGName } | Remove-AzResource -force | Out-Null
    # The before-mentioned forced delete of the OS disk for the restored VM
    Write-Host -ForegroundColor Cyan "Attempting forced remove of OS disk: $OSDiskResourceID"
    Remove-AzResource -ResourceId $OSDiskResourceID -Force
    foreach ($dd in $data_disk_array) {
        Write-Host -ForegroundColor Cyan "Attempting forced remove of data disk: $dd"
        Remove-AzResource -ResourceId $dd -Force
    }
    Write-Host -ForegroundColor Green 'Azure Virtual Machine-' $VMName 'and all the resources associated with the VM were removed sucesfully...'
}
else {
    Write-Host -ForegroundColor Red "The VM name entered doesn't exist in your connected Azure Tenant! Kindly check the name entered and restart the script with correct VM name..."
}