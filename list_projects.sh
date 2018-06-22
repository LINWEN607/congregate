#!/bin/bash

config=$(cat config.json | jq '.config')
host=$(echo $config | jq -r '.child_instance_host')
token=$(echo $config | jq -r '.child_instance_token')

out=$(curl -s --request GET --header "PRIVATE-TOKEN: $token" $host/api/v4/projects)
project_info=$(echo $out | jq '[.[] | {id: .id, name: .name, name_with_namespace: .name_with_namespace, description: .description}]')
for ((i=0;i<`echo $project_info | jq '. | length'`;i++)); do
    name=$(echo $project_info | jq ".[$i] .name" | tr -d \")
    description=$(echo $project_info | jq ".[$i] .description" | tr -d \")
    corrected_number=$((i+1))
    echo "$corrected_number. $name: $description"
done