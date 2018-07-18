#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2018 - GitLab
#
# Bash script to list all projects within the child instance
#

config=$(cat ${CONGREGATE_PATH}/data/config.json | jq '.config')
host=$(echo $config | jq -r '.child_instance_host')
token=$(echo $config | jq -r '.child_instance_token')

echo "Listing projects from $host"

out=$(curl -s --request GET --header "PRIVATE-TOKEN: $token" $host/api/v4/projects)

echo $out | jq . > ${CONGREGATE_PATH}/data/project_json.json

# Printing output to screen
project_info=$(echo $out | jq '[.[] | {id: .id, name: .name, name_with_namespace: .name_with_namespace, description: .description}]')
for ((i=0;i<`echo $project_info | jq '. | length'`;i++)); do
    name=$(echo $project_info | jq -r ".[$i] .name_with_namespace")
    description=$(echo $project_info | jq -r ".[$i] .description")
    id=$(echo $project_info | jq -r ".[$i] .id")
    corrected_number=$((i+1))
    nt=$'\n'
    echo "[id: $id] $name: $description"
done

# Retrieve user info from child instance
${CONGREGATE_PATH}/group_cleanup.sh

# Retrieve group info from child instance
${CONGREGATE_PATH}/user_cleanup.sh
