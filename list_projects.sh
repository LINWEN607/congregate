#!/bin/bash

config=$(cat config.json | jq '.config')
host=$(echo $config | jq -r '.child_instance_host')
token=$(echo $config | jq -r '.child_instance_token')

echo "Listing projects from $host"

out=$(curl -s --request GET --header "PRIVATE-TOKEN: $token" $host/api/v4/projects?simple=true)

echo $out | jq . > project_json.json

project_info=$(echo $out | jq '[.[] | {id: .id, name: .name, name_with_namespace: .name_with_namespace, description: .description}]')
for ((i=0;i<`echo $project_info | jq '. | length'`;i++)); do
    name=$(echo $project_info | jq -r ".[$i] .name_with_namespace")
    description=$(echo $project_info | jq -r ".[$i] .description")
    id=$(echo $project_info | jq -r ".[$i] .id")
    corrected_number=$((i+1))
    nt=$'\n'
    echo "[id: $id] $name: $description"
done


users=$(curl -s --request GET --header "PRIVATE-TOKEN: $token" $host/api/v4/users | jq 'del(.[] | select(.id == 1))')
jsonArray=$(jq -n '[]')
for ((i=0;i<`echo $users | jq '. | length'`;i++));
do
    cleanup=$(echo $users | jq ".[$i] | del(.web_url, .last_sign_in_at, .last_activity_at, .current_sign_in_at, .can_create_project, .two_factor_enabled, .avatar_url, .created_at, .id)")
    jsonArray=$(echo $jsonArray | jq --argjson i "$cleanup" '. += [$i]')
done

echo $jsonArray | jq . > users.json