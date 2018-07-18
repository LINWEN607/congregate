#!/bin/bash

config=$(cat ${CONGREGATE_PATH}/data/config.json | jq '.config')
host=$(echo $config | jq -r '.child_instance_host')
token=$(echo $config | jq -r '.child_instance_token')

echo "Listing projects from $host"

out=$(curl -s --request GET --header "PRIVATE-TOKEN: $token" $host/api/v4/projects)

echo $out | jq . > ${CONGREGATE_PATH}/data/project_json.json

project_info=$(echo $out | jq '[.[] | {id: .id, name: .name, name_with_namespace: .name_with_namespace, description: .description}]')
for ((i=0;i<`echo $project_info | jq '. | length'`;i++)); do
    name=$(echo $project_info | jq -r ".[$i] .name_with_namespace")
    description=$(echo $project_info | jq -r ".[$i] .description")
    id=$(echo $project_info | jq -r ".[$i] .id")
    corrected_number=$((i+1))
    nt=$'\n'
    echo "[id: $id] $name: $description"
done

${CONGREGATE_PATH}/group_cleanup.sh

${CONGREGATE_PATH}/user_cleanup.sh
