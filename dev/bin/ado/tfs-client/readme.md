# TFS Client

> This tool is in BETA state, limited support.

The **TFS Client** is a command-line utility for retrieving user lists from a TFS (Team Foundation Server) or Azure DevOps Server instance.

## Build the project

To compile and build the project, follow these steps:

    ```sh
    cd ./dev/bin/ado/tfs-client # (if not in the directory yet)
    dotnet restore
    dotnet build
    ```

## Usage

    ```sh

    cd ./bin/Debug/net472
    Getuserlist <TFS Uri> <username> <PAT>

    ```

- `<TFS Uri>`: The URL of your TFS/Azure DevOps Server (e.g., `http://tfs.example.com:8080/tfs/DefaultCollection`)
- `<username>`: Your TFS/Azure DevOps username
- `<PAT>`: Your Personal Access Token

## Example

    ```sh

    Getuserlist http://tfs.example.com:8080/tfs/DefaultCollection user@example.com mypat123
  
    ```

The output is in file `users.json` and has the following format: 

    ```json

    [{
      "email": "email@example.io",
      "id": "win.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm",
      "name": "John Doe",
      "state": "active",
      "username": "john.doe"
    }]

    ```

## Description

This tool authenticates to the specified TFS/Azure DevOps Server using the provided credentials and retrieves the list of users in the "Project Collection Valid Users" group. The output is a list of users that are compatible with json files in congregate (e.g. you can add them to `users.json`, `projects.json` and `groups.json` to create users and preserve contributions)

## Requirements

- .NET Framework 4.7.2
- Access to the TFS/Azure DevOps Server
- A valid Personal Access Token (PAT) with admin permissions.
